# Systems & Engineering Practice Exploration (Part C)

**Author:** Dilawar khan  
**Roll Number:** TRN-2026-000961  
**Date:** 17 Nov 2026  
**Assignment:** Reproducible Data Pipelines, Tabular ML & Systems Exploration  

---

## Topic C1: Optimized Query System of a Social Media Algorithm

### 1. Architectural Exploration: Candidate Retrieval, Indexing, and Caching
Serving a social media feed with sub-100ms latency across hundreds of millions of users requires decoupling raw database storage from real-time timeline presentation. A production feed pipeline typically operates in three distinct stages:
1. **Candidate Retrieval:** Finding the pool of candidate posts from followed authors, groups, or recommendation systems.
2. **Scoring & Ranking:** Evaluating each candidate post using engagement probabilities (likes, comments, recency, relevance).
3. **Pagination & Hydration:** Slicing the top $K$ posts and hydrating IDs with user avatars, media URLs, and comment counts.

#### Fan-Out on Read (Pull Model) vs. Fan-Out on Write (Push Model)
* **Fan-Out on Read (Pull):** When a user requests their timeline, the system executes a real-time relational query joining the user's following list with the posts table.
  * *Pros:* Zero write amplification; publishing a post requires only a single row insertion.
  * *Cons:* Read latency explodes when users follow hundreds or thousands of active accounts; every page refresh triggers expensive disk I/O and sorting.
* **Fan-Out on Write (Push):** When an author publishes a post, asynchronous workers (e.g. via Celery, Kafka, or RabbitMQ) iterate through all of the author's followers and push the post ID into each follower's precomputed timeline cache (e.g., a Redis Sorted Set keyed by `user_feed:{user_id}`).
  * *Pros:* Reading a feed is an instant $O(1)$ or $O(K)$ in-memory operation (`ZREVRANGEBYSCORE`).
  * *Cons:* Severe write amplification. If a celebrity with 50 million followers posts, pushing 50 million cache writes consumes massive cluster memory and network bandwidth.
* **Hybrid Industry Architecture (Twitter/X & Instagram):** Standard users use **Fan-Out on Write**. However, for "celebrity" accounts with $>50,000$ followers, the system uses **Fan-Out on Read**: their posts are not pushed to 50M caches; instead, their recent posts are dynamically blended into the user's cached timeline at read time.

---

### 2. Experimental Verification: SQLite Benchmark Results
To empirically measure the effect of database indexing on feed retrieval, we executed an experiment on a synthetic dataset of **500 users, 5,000 follow relationships, and 50,000 posts** (`src/exploration_c1.py`):

```sql
SELECT p.post_id, p.author_id, p.content, p.likes_count, p.created_at
FROM posts p
INNER JOIN follows f ON p.author_id = f.followee_id
WHERE f.follower_id = 1
ORDER BY p.created_at DESC
LIMIT 20;
```

#### Empirical Results & EXPLAIN QUERY PLAN

| Configuration | EXPLAIN QUERY PLAN Output | Mean Execution Latency (10 runs) | Speedup Factor |
| :--- | :--- | :--- | :--- |
| **Unindexed (Scan)** | `SCAN p`<br>`SEARCH f USING COVERING INDEX sqlite_autoindex_follows_1`<br>`USE TEMP B-TREE FOR ORDER BY` | **50.632 ms** | Baseline ($1.0\times$) |
| **Composite Index** `(author_id, created_at DESC)` | `SEARCH f USING COVERING INDEX idx_follows_follower`<br>`SEARCH p USING INDEX idx_posts_author_created`<br>`USE TEMP B-TREE FOR ORDER BY` | **1.011 ms** | **$50.1\times$ Faster** |

#### Answers to Guiding Questions:
* **Why is a naive join slow at scale?** Without indexes, the database engine must execute a sequential scan (`SCAN p`) inspecting all 50,000 rows, evaluating the join condition, and buffering candidates in a temporary on-disk B-Tree to execute `ORDER BY created_at DESC`. At 100M rows, this results in seconds of disk thrashing.
* **What does an index on `(author_id, created_at DESC)` change?** The composite B-tree index clusters posts by author and pre-sorts them by timestamp. The engine performs targeted logarithmic index seeks (`SEARCH p USING INDEX`) directly accessing only the relevant author's records already in chronological order.
* **When would you precompute feeds instead?** When read volume vastly exceeds write volume (e.g. 99% of social app interactions are scrolling/reading feeds), precomputing feeds into Redis memory caches eliminates relational query overhead entirely.

---

### 3. Bonus Challenge (+2): Tiny Feed Ranker
We implemented an algorithmic ranking function scoring retrieved candidates by engagement and exponential temporal decay:

$$\text{Score} = (\text{likes\_count} \times 0.4) + \left(\frac{1000}{1 + \frac{\text{Age in Hours}}{24}} \times 0.6\right)$$

In our benchmark, candidate retrieval and scoring for 200 posts completed in **4.268 ms**, surfacing high-engagement, fresh content at the top of the user's feed (`outputs/reports/c1_experiment_results.txt`).

---

## Topic C2: GitHub Actions, Branch Rules, and Code Reviews

### 1. CI Workflow Architecture (`.github/workflows/ci.yml`)
Continuous Integration enforces deterministic quality gates before code enters `main`:
* **Triggers:** Evaluates all `push` events to `main` and all `pull_request` events targeting `main`.
* **Execution Environment:** `ubuntu-latest` running Python 3.13.
* **Job Steps:**
  1. `actions/checkout@v4` fetches source code.
  2. `actions/setup-python@v5` with `cache: 'pip'` accelerates rebuilds by preserving cached wheels.
  3. `pip install -r requirements.txt` installs exact dependencies.
  4. Flake8 linter catches undefined symbols (`F82`), syntax errors (`E9`), and structural defects.
  5. `pytest tests/ -v` executes the complete test suite.

### 2. Branch Protection Rules & Merge Gates
In enterprise engineering, the `main` branch is protected with strict rules:
1. **Require Pull Request Reviews:** Direct commits to `main` are rejected. At least one approving review is mandatory.
2. **Require Status Checks to Pass:** The CI job (`test-and-lint`) must report green before the "Merge" button is unlocked.
3. **Require Linear History:** Disallows merge commits in favor of Squash & Merge or Rebase to preserve a clean, bisectable Git history.
4. **Code Owners (`CODEOWNERS`):** Critical files (e.g. `src/validate.py`, `models/`, `.github/workflows/`) require sign-off from designated senior engineers to prevent unauthorized security or pipeline bypasses.

### 3. What a High-Quality Code Review Looks Like
A constructive review focuses on correctness, architecture, and maintainability:
* **Scope Check:** Does the PR do one thing well, or is it an unfocused 2,000-line diff?
* **Defensive Edge Cases:** Are nulls, division by zero, and network timeouts handled gracefully?
* **Leakage & Bias:** In ML pipelines, are scalers fitted exclusively on training splits?
* **Clarity:** Are variable names intuitive? Are complex equations documented?

---

## Topic C3: Theory of System Design

### 1. Glossary of 10 Core Architectural Terms

| # | System Design Term | Definition | Concrete Real-World Example |
| :--- | :--- | :--- | :--- |
| 1 | **Load Balancer** | Distributes incoming network traffic evenly across a pool of backend servers to prevent bottlenecks. | **AWS Application Load Balancer (ALB)** routing web requests across auto-scaling EC2 instances. |
| 2 | **Horizontal vs. Vertical Scaling** | Vertical scaling adds CPU/RAM to a single node; Horizontal scaling adds more independent server nodes. | Upgrading from `t3.medium` to `m5.4xlarge` (Vertical) vs adding 10 container replicas behind Kubernetes (Horizontal). |
| 3 | **Distributed Cache** | High-speed, in-memory data store accessible across multiple application servers for fast reads. | **Redis Cluster** caching user authentication sessions and popular feed items. |
| 4 | **Database Sharding** | Horizontally partitioning rows of a large database across separate database servers by a shard key. | Sharding a messaging database by `user_id % 16` across 16 PostgreSQL database instances. |
| 5 | **Message Queue** | An asynchronous buffer decouples producers from consumers, enabling background processing and backpressure handling. | **Apache Kafka** or **RabbitMQ** buffering photo uploads while image-resizing worker services process them. |
| 6 | **Database Replication** | Synchronizing data from a primary database node to read-only replicas to improve read throughput and fault tolerance. | **PostgreSQL Streaming Replication** with 1 Primary for writes and 3 Read Replicas for queries. |
| 7 | **Idempotency** | The property of an operation where executing it multiple times produces the identical state as executing it once. | A payment API checking `Idempotency-Key: <UUID>` so network retries do not charge the customer's credit card twice. |
| 8 | **Heartbeat / Health Check** | Periodic signals sent between distributed nodes to verify availability and trigger automated failovers. | Kubernetes `readinessProbe` and `livenessProbe` checking HTTP `/healthz` endpoints. |
| 9 | **Rate Limiter** | Throttles incoming client requests to protect upstream infrastructure from denial of service and noisy neighbors. | **Token Bucket / Leaky Bucket** algorithm in Cloudflare or NGINX limiting clients to 100 requests per minute. |
| 10| **Reverse Proxy** | Sits in front of web servers, intercepting client requests to handle SSL termination, compression, and security shielding. | **NGINX** or **HAProxy** terminating TLS certificates and forwarding plain HTTP traffic to backend Docker containers. |

### 2. Deep-Dive Trade-Off: Strong Consistency vs. High Availability (CAP / PACELC)
Under Eric Brewer's **CAP Theorem** (and the extended **PACELC Theorem**), a distributed data store operating over an unreliable network partition ($P$) must choose between **Consistency ($C$)** (every read receives the most recent write or an error) and **Availability ($A$)** (every non-failing node returns a response, but it may contain stale data). In latency-sensitive systems like social feeds or e-commerce product catalogs, teams choose **Eventual Consistency (AP)**: returning a slightly outdated timeline or inventory count within 50 milliseconds is far superior to throwing an HTTP 500 error or stalling user navigation. Conversely, in core financial transaction ledgers or booking systems, teams choose **Strong Consistency (CP)**: operations block and wait for consensus (e.g. via Paxos or Raft) because returning incorrect account balances or double-booking airline seats causes irreversible data corruption.

---

## Topic C4: A Repeatable Workflow for System Design

### 1. Repeatable 5-Step System Design Workflow

```text
[Step 1: Clarify Requirements & Scope]
  ├── Functional requirements (What the system does)
  └── Non-functional requirements (Scale, latency, throughput, SLA)
              │
              ▼
[Step 2: Capacity Estimation & Back-of-the-Envelope Math]
  ├── Read/Write QPS, bandwidth, and storage growth over 5 years
              │
              ▼
[Step 3: High-Level Architecture & API Design]
  ├── Client -> CDN -> Load Balancer -> Web App -> Cache / DB
              │
              ▼
[Step 4: Detailed Component Design & Data Modeling]
  ├── Relational vs NoSQL schema, index design, message queues
              │
              ▼
[Step 5: Bottlenecks, Fault Tolerance & Trade-Offs]
  └── Single Points of Failure, replication lag, partitioning, rate limiting
```

### 2. Concrete System Design Document: Scalable URL Shortener (TinyURL)

#### 1. Requirements & Scope
* **Functional Requirements:**
  1. Given a long URL, return a unique 7-character short URL (e.g., `https://tiny.cc/aB3x9Z`).
  2. Clicking the short URL redirects the user via HTTP 301/302 to the original destination.
  3. Custom alias support and URL expiration (default: 5 years).
* **Non-Functional Requirements:**
  1. High availability ($99.99\%$) with read latency $< 30\text{ ms}$.
  2. 100:1 read-to-write ratio (heavily read-intensive).

#### 2. Capacity Estimation
* **Write Throughput:** 100 Million new URLs created per month $\approx 40\text{ writes/sec}$.
* **Read Throughput:** 10 Billion redirections per month $\approx 4,000\text{ reads/sec}$ (Peak: $8,000\text{ QPS}$).
* **Storage Calculation (5 Years):**
  $100\text{M} \times 12 \times 5 = 6\text{ Billion records}$.
  Assuming 500 bytes per record (Original URL + Short Key + User ID + Timestamps):
  $$6\text{ Billion} \times 500\text{ bytes} \approx 3\text{ Terabytes total storage (easily manageable)}.$$
* **Cache Memory (80/20 Rule):**
  Cache 20% of daily read volume ($20\% \times \frac{10\text{B}}{30} \times 500\text{ bytes} \approx 33\text{ GB RAM}$). A single Redis node can hold the entire working set.

#### 3. Short Key Generation Architecture
To generate unique 7-character keys using Base62 encoding (`[a-zA-Z0-9]`, $62^7 \approx 3.5\text{ Trillion}$ combinations):
* **Approach:** Distributed Key Generation Service (KGS) running Apache ZooKeeper.
* *How it works:* The KGS pre-generates sequential integer ranges (e.g. Server 1 gets range 1M–2M, Server 2 gets 2M–3M). Servers convert IDs to Base62 strings locally in memory without database collisions or hash lock contention.

#### 4. Data Storage & Schema
A NoSQL Key-Value Store (**Amazon DynamoDB** or **Cassandra**) is optimal:
* **Table:** `url_mappings`
  * `short_key` (Partition Key, String, 7 chars)
  * `original_url` (String, up to 2048 chars)
  * `user_id` (UUID)
  * `created_at` (Timestamp)
  * `expires_at` (Timestamp, with TTL auto-purge)

#### 5. End-to-End Request Flow
1. User requests `GET /aB3x9Z`.
2. Cloudflare CDN / Redis Cache checks for key `aB3x9Z`. If cached, returns HTTP 302 redirect in $<5\text{ ms}$.
3. On cache miss, queries DynamoDB by primary key `short_key`, populates Redis cache, and returns HTTP 302.
4. Asynchronous click events are dispatched to a Kafka queue for analytics aggregation without blocking the redirect.
