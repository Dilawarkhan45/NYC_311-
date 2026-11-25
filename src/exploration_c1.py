# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
Part C1: Social Media Feed Query Optimization & Tiny Feed Ranker (Bonus +2).
Compares query execution plans, indexing strategies, and caching for social feed generation.
Outputs timings, EXPLAIN QUERY PLAN analysis, and ranked feed outputs.
"""

import os
import sys
import time
import sqlite3
import random
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "outputs", "reports", "c1_experiment_results.txt")

def setup_social_database(conn: sqlite3.Connection, num_users=500, num_follows=5000, num_posts=50000):
    """Creates schema and seeds synthetic social network data."""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS posts;")
    cursor.execute("DROP TABLE IF EXISTS follows;")
    cursor.execute("DROP TABLE IF EXISTS users;")
    
    cursor.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE follows (
        follower_id INTEGER NOT NULL,
        followee_id INTEGER NOT NULL,
        PRIMARY KEY (follower_id, followee_id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE posts (
        post_id INTEGER PRIMARY KEY,
        author_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        likes_count INTEGER NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    
    # Seed users
    users = [(i, f"user_{i}") for i in range(1, num_users + 1)]
    cursor.executemany("INSERT INTO users VALUES (?, ?);", users)
    
    # Seed follows (User 1 follows 100 users for benchmark)
    random.seed(42)
    follows = set()
    for f in range(2, 102):
        follows.add((1, f))
    while len(follows) < num_follows:
        u1 = random.randint(1, num_users)
        u2 = random.randint(1, num_users)
        if u1 != u2:
            follows.add((u1, u2))
    cursor.executemany("INSERT INTO follows VALUES (?, ?);", list(follows))
    
    # Seed posts
    base_time = datetime(2026, 11, 1, 0, 0, 0)
    posts = []
    for pid in range(1, num_posts + 1):
        author = random.randint(1, num_users)
        likes = random.randint(0, 1500)
        dt = base_time + timedelta(minutes=random.randint(0, 40000))
        posts.append((pid, author, f"Post content #{pid}", likes, dt.isoformat()))
    cursor.executemany("INSERT INTO posts VALUES (?, ?, ?, ?, ?);", posts)
    conn.commit()

def run_experiment():
    """Executes indexing benchmark, EXPLAIN QUERY PLAN, and tiny feed ranker."""
    conn = sqlite3.connect(":memory:")
    print("[INFO] Generating synthetic social dataset (500 users, 5,000 follows, 50,000 posts)...")
    setup_social_database(conn)
    cursor = conn.cursor()
    
    output_lines = [
        "==========================================================================",
        "PART C1: SOCIAL FEED QUERY OPTIMIZATION & FEED RANKER EXPERIMENT",
        "Author: Dilawar khan | Roll: TRN-2026-000961 | Date: 17 Nov 2026",
        "==========================================================================",
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Database scale: 500 users | 5,000 follow edges | 50,000 posts",
        ""
    ]
    
    feed_query = """
    SELECT p.post_id, p.author_id, p.content, p.likes_count, p.created_at
    FROM posts p
    INNER JOIN follows f ON p.author_id = f.followee_id
    WHERE f.follower_id = 1
    ORDER BY p.created_at DESC
    LIMIT 20;
    """
    
    # -------------------------------------------------------------------------
    # Experiment 1A: Query WITHOUT Indexes
    # -------------------------------------------------------------------------
    output_lines.append("--- 1. BENCHMARK WITHOUT INDEX (FULL TABLE SCAN) ---")
    cursor.execute(f"EXPLAIN QUERY PLAN {feed_query}")
    plan_no_index = cursor.fetchall()
    for row in plan_no_index:
        output_lines.append(f"  EXPLAIN: {row}")
        
    times_no_idx = []
    for _ in range(10):
        t0 = time.perf_counter()
        cursor.execute(feed_query)
        _ = cursor.fetchall()
        times_no_idx.append((time.perf_counter() - t0) * 1000)
        
    avg_no_idx = sum(times_no_idx) / len(times_no_idx)
    output_lines.append(f"Execution Time (Unindexed): {avg_no_idx:.3f} ms (Mean over 10 runs)")
    output_lines.append("")
    
    # -------------------------------------------------------------------------
    # Experiment 1B: Query WITH Composite Index
    # -------------------------------------------------------------------------
    output_lines.append("--- 2. BENCHMARK WITH COMPOSITE INDEXES ---")
    cursor.execute("CREATE INDEX idx_follows_follower ON follows(follower_id, followee_id);")
    cursor.execute("CREATE INDEX idx_posts_author_created ON posts(author_id, created_at DESC);")
    conn.commit()
    
    cursor.execute(f"EXPLAIN QUERY PLAN {feed_query}")
    plan_with_index = cursor.fetchall()
    for row in plan_with_index:
        output_lines.append(f"  EXPLAIN: {row}")
        
    times_with_idx = []
    for _ in range(10):
        t0 = time.perf_counter()
        cursor.execute(feed_query)
        _ = cursor.fetchall()
        times_with_idx.append((time.perf_counter() - t0) * 1000)
        
    avg_with_idx = sum(times_with_idx) / len(times_with_idx)
    speedup = avg_no_idx / max(avg_with_idx, 0.0001)
    output_lines.append(f"Execution Time (Indexed): {avg_with_idx:.3f} ms (Mean over 10 runs)")
    output_lines.append(f"Query Acceleration / Speedup: {speedup:.1f}x faster with index!")
    output_lines.append("")
    
    # -------------------------------------------------------------------------
    # Challenge Bonus (+2): Tiny Feed Ranker
    # -------------------------------------------------------------------------
    output_lines.append("--- 3. BONUS CHALLENGE (+2): TINY FEED RANKER ---")
    output_lines.append("Ranking Function: score = (likes_count * 0.4) + (recency_decay * 0.6)")
    
    # Retrieve candidates using indexed query
    t_rank_start = time.perf_counter()
    cursor.execute("""
    SELECT p.post_id, p.author_id, p.content, p.likes_count, p.created_at
    FROM posts p
    INNER JOIN follows f ON p.author_id = f.followee_id
    WHERE f.follower_id = 1
    ORDER BY p.created_at DESC
    LIMIT 200;
    """)
    candidates = cursor.fetchall()
    
    ref_time = datetime(2026, 11, 28, 0, 0, 0)
    scored_posts = []
    for post in candidates:
        pid, author, content, likes, created_str = post
        created_dt = datetime.fromisoformat(created_str)
        hours_old = max(0.1, (ref_time - created_dt).total_seconds() / 3600.0)
        recency_score = 1000.0 / (1.0 + (hours_old / 24.0)) # Exponential-like decay
        final_score = (likes * 0.4) + (recency_score * 0.6)
        scored_posts.append((final_score, pid, author, likes, hours_old, content))
        
    scored_posts.sort(key=lambda x: x[0], reverse=True)
    top_10 = scored_posts[:10]
    rank_time_ms = (time.perf_counter() - t_rank_start) * 1000
    
    output_lines.append(f"Ranking Compute Latency: {rank_time_ms:.3f} ms for 200 candidates")
    output_lines.append("\nTop 10 Ranked Feed Items for User 1:")
    output_lines.append(f"{'Rank':<5} {'Score':<10} {'PostID':<8} {'Author':<8} {'Likes':<8} {'Age (hrs)':<10} Content")
    output_lines.append("-" * 75)
    for r, item in enumerate(top_10, 1):
        score, pid, author, likes, age, content = item
        output_lines.append(f"{r:<5} {score:<10.2f} {pid:<8} {author:<8} {likes:<8} {age:<10.1f} {content}")
        
    output_lines.extend([
        "",
        "--- 4. CACHING & ARCHITECTURAL SUMMARY ---",
        "1. Indexing Impact: The composite index on (author_id, created_at DESC) transforms a high-cost",
        "   table scan (SCAN TABLE posts) with B-tree temporary sorting into an indexed B-tree search",
        "   (SEARCH posts USING INDEX idx_posts_author_created), yielding a massive query speedup.",
        "2. Fan-out on Write vs. Fan-out on Read:",
        "   - Fan-out on Read (Current experiment): Computes the feed dynamically at query time by joining",
        "     the follows table. Simple writes, but high read latency at scale.",
        "   - Fan-out on Write (Push Model): When an author posts, a background queue pushes the post ID",
        "     into the precomputed feed caches (e.g. Redis Sorted Sets) of all active followers.",
        "   - Hybrid Strategy: Standard users use Fan-out on Write; high-follower celebrity accounts",
        "     (>100k followers) use Fan-out on Read to avoid catastrophic write amplification."
    ])
    
    full_output = "\n".join(output_lines)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(full_output)
        
    print(full_output)
    print(f"\n[SUCCESS] C1 Experiment report saved to: {OUTPUT_PATH}")
    conn.close()

if __name__ == "__main__":
    run_experiment()
