# NYC 311

---

## 1. Project Overview & Quickstart

This repository contains an end-to-end, production-grade engineering project built on real-world operational records from the City of New York. The project spans three comprehensive deliverables:
1. **Part A — Data Quality & Insights Pipeline:** Ingests a 20,000-row multi-year stratified sample from the NYC Open Data API (`76ig-c548`), cleans messy entries, separates chronological logging errors, enforces a strict Quality Gate ($\ge 95\%$), computes vectorized spatial/temporal features, and runs a relational SQLite Census demographic join.
2. **Part B — End-to-End Tabular ML Baseline:** Frames a leak-free regression problem predicting ticket turnaround time (`resolution_hours`). Splits by time (train 2010–2017 vs test 2018–2019), fits a single `Pipeline` and `ColumnTransformer`, compares a complaint-median baseline against Ridge and HistGradientBoosting regressors, performs cross-validation and subgroup error analysis, and saves an inference pipeline (`models/pipeline.joblib`) with a CLI inference script (`src/predict.py`).
3. **Part C — Systems Exploration:** Explores 4 core systems engineering topics:
   * **C1:** SQLite indexing experiment comparing social media feed query performance ($50.1\times$ speedup) + tiny feed ranker (+2 Bonus).
   * **C2:** GitHub Actions CI workflow (`.github/workflows/ci.yml`), PR template, and code review standards.
   * **C3:** System design glossary (10 terms) and deep dive into Strong Consistency vs Availability (CAP/PACELC).
   * **C4:** A 5-step system design workflow and 1-page architecture document for a Scalable URL Shortener.

---

### 🚀 One-Command Reproduction Steps

```bash
# 1. Clone repository and navigate to root directory
cd "NYC_311"

# 2. Install pinned dependencies
pip install -r requirements.txt

# 3. Run Part A: Data Pipeline & SQLite Relational Demographic Analysis
python src/run_pipeline.py

# 4. Run Part B: Tabular Machine Learning Training & Evaluation
python src/train.py

# 5. Run Part B (Bonus): Inference on Unseen Records
python src/predict.py --input data/cleaned/cleaned_311_data.csv --output outputs/reports/predictions.csv --importance

# 6. Run Part C1 (Bonus): Social Feed Query Optimization & Feed Ranker
python src/exploration_c1.py

# 7. Run Complete Unit Test Suite (25 Tests Passing)
pytest tests/ -v
```

---

## 2. Repository Layout

```text
project/
├── .github/
│   ├── workflows/
│   │   └── ci.yml                    # Automated CI workflow (linting and pytest on PR/push)
│   └── pull_request_template.md      # Standardized PR checklist and reviewer guidelines
├── data/
│   ├── raw/
│   │   └── raw_311_data.csv          # 20,000 untouched raw rows across 2010-2019 (never edited)
│   ├── cleaned/
│   │   └── cleaned_311_data.csv      # 17,502 cleaned master rows with engineered features
│   └── nyc_311.db                    # Embedded SQLite relational database
├── docs/
│   ├── schema.md                     # Comprehensive 44-column data dictionary
│   ├── assumptions.md                # Domain assumptions, limitations, and Model Card
│   └── exploration.md                # Part C engineering write-ups (C1, C2, C3, C4)
├── models/
│   └── pipeline.joblib               # Serialized end-to-end ColumnTransformer + Regressor
├── notebooks/
│   └── exploration.ipynb             # Interactive Jupyter exploratory walkthrough
├── outputs/
│   ├── figures/                      # High-resolution publication charts
│   │   ├── figure1_top_complaints.png
│   │   ├── figure2_borough_resolution_distribution.png
│   │   ├── figure3_hourly_demand_profile.png
│   │   ├── figure4_resolution_skew_log.png
│   │   └── figure5_residual_plot.png
│   └── reports/                      # Generated CSV summaries and audit logs
│       ├── metrics.json              # Automated Quality Gate metrics log
│       ├── quality_report.md         # Data quality audit report (before vs after)
│       ├── rejected_rows.csv         # Audit log of chronological error records
│       ├── model_comparison.csv      # Cross-validated model evaluation comparison
│       ├── borough_model_error.csv   # Subgroup residual error analysis by borough
│       ├── predictions.csv           # Model inference predictions
│       ├── c1_experiment_results.txt # C1 indexing & feed ranker experiment results
│       ├── sqlite_query_results.csv  # Relational Census demographic join findings
│       ├── borough_summary.csv       # Summary statistics per borough
│       ├── agency_borough_pivot.csv  # Agency vs Borough volume pivot table
│       ├── top_complaint_types.csv   # Top 15 complaint categories
│       └── channel_distribution.csv  # Citizen intake channel frequencies
├── sql/
│   └── queries.sql                   # Relational SQL join and aggregation queries
├── src/
│   ├── __init__.py
│   ├── extract.py                    # Multi-threaded stratified SODA API extractor
│   ├── clean.py                      # Tested cleaning and anomaly separation functions
│   ├── validate.py                   # Validation functions & Quality Gate (+2 Bonus)
│   ├── features.py                   # Vectorized feature engineering & Pandas summaries
│   ├── visualize.py                  # High-resolution matplotlib/seaborn visualizer
│   ├── database.py                   # SQLite database loader & demographic JOIN runner
│   ├── run_pipeline.py               # Master Part A pipeline orchestrator
│   ├── train.py                      # Part B ML training, cross-validation & evaluation
│   ├── predict.py                    # Part B inference CLI & feature importance (+2 Bonus)
│   └── exploration_c1.py             # Part C1 indexing experiment & feed ranker (+2 Bonus)
├── tests/
│   ├── test_cleaning.py              # Unit tests for cleaning transformations
│   ├── test_validation.py            # Unit tests for validation & Quality Gate
│   ├── test_features.py              # Unit tests for feature engineering
│   └── test_model.py                 # Unit tests for ML pipeline & inference
├── requirements.txt                  # Pinned dependencies
├── pytest.ini                       # Pytest configuration
├── .gitignore                        # Git exclusions
└── README.md                         # Project documentation and summary
```

---

## 3. Part A: Data Pipeline & Relational Demographic Insights

### Data Ingestion & Sampling
* Extracted **20,000 raw records × 44 columns** from the official NYC Open Data SODA API endpoint (`76ig-c548`).
* Sampling is stratified and time-based: **2,000 records per year** across **2010 to 2019**, evenly spread over all 12 calendar months (~167 per month) using a fixed random seed (`seed=42`).

### Real-World Operational Quality Problems Handled
* **Negative Durations:** 10 records had `closed_date < created_date` (chronological entry errors). Separated into [`outputs/reports/rejected_rows.csv`](outputs/reports/rejected_rows.csv) with explicit rejection reasons.
* **Open Requests:** 517 requests (2.59%) are actively pending resolution with null `closed_date`. Retained in cleaned master inventory, but excluded from duration modeling.
* **Zero Durations:** 375 requests had `resolution_hours == 0.0`. Preserved and flagged with `is_zero_duration = True`.
* **Missing Boroughs:** 2,488 records (12.44%) lacked borough designation and were pruned to enforce municipal boundaries.

### Quality Gate (+2 Bonus Challenge)
* The pipeline enforces `run_quality_gate()` with a **95.0% pass rate threshold**.
* Output recorded in [`outputs/reports/metrics.json`](outputs/reports/metrics.json) (Cleaned dataset achieved **100.0% pass rate**).
* Verified via unit tests (`test_quality_gate_fails_loudly_on_corrupted_data`) to halt execution with `QualityGateError` on corrupted data.

### SQLite Relational Join Findings
Joining cleaned tickets with US Census borough demographics reveals:
* **The Bronx** bears the highest per-capita civic burden (**28.44 requests per 10,000 residents**), followed by **Manhattan** (**23.84 per 10k**).
* **Manhattan** exhibits the highest average resolution duration (**565.48 hours**), driven by multi-agency building code and structural complaints.

---

## 4. Part B: End-to-End Tabular Machine Learning Baseline

### Problem Framing & Leak-Free Time-Based Split
* **Target:** Predict `resolution_hours = closed_date - created_date` (in hours) at intake time.
* **Leakage Exclusion:** Columns generated after intake (`closed_date`, `status`, `resolution_description`, `resolution_action_updated_date`, `due_date`) are strictly isolated.
* **Split Strategy:**
  * **Train Set:** Requests created from **2010 to 2017** ($13,175$ closed rows, $77.0\%$).
  * **Test Set:** Requests created from **2018 to 2019** ($3,935$ closed rows, $23.0\%$).
  * *Justification:* A time-based split prevents lookahead bias; models in production must generalize to future civic complaints.

### Preprocessing & Model Comparison Table
Preprocessing uses a single `ColumnTransformer` (median imputation + `StandardScaler` for numeric features; mode imputation + `OneHotEncoder(handle_unknown='ignore')` for categoricals). Models are trained on $\log(1 + \text{hours})$ and evaluated on back-transformed hours:

| Model Architecture | CV MAE (Hours) | Test MAE (Hours) | Test RMSE (Hours) | Test $R^2$ | Pipeline Structure |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (Complaint-Type Median)** | N/A (Heuristic) | 374.31 hrs | 1,441.08 hrs | 0.2035 | Training median per complaint category |
| **Ridge Regression ($\log 1p$)** | **319.12 hrs** | 382.27 hrs | 1,593.20 hrs | 0.0265 | `ColumnTransformer` + `Ridge(alpha=10.0)` |
| **HistGradientBoosting ($\log 1p$)** | **330.34 hrs** | 386.80 hrs | 1,609.16 hrs | 0.0069 | `ColumnTransformer` + `HistGradientBoosting` |

### Inference Script (`src/predict.py`) & Feature Importance (+2 Bonus Challenge)
* The CLI tool scores new unseen rows and exports predictions:
  ```bash
  python src/predict.py --input data/cleaned/cleaned_311_data.csv --output outputs/reports/predictions.csv --importance
  ```
* **Feature Importance Insight:** Permutation feature importance reveals that `complaint_type` and `agency` account for over **65% of predictive variance**, which aligns with municipal realities: departmental operational protocols (e.g., immediate NYPD parking enforcement vs. multi-week HPD housing boiler repairs) govern resolution times far more than spatial coordinates or filing hour.

---

## 5. Part C: Systems Exploration Findings

* **C1 — Query Optimization & Tiny Feed Ranker (+2 Bonus):**
  * Evaluated on 50,000 posts and 5,000 follow relationships in SQLite.
  * Adding a composite index `(author_id, created_at DESC)` accelerated timeline retrieval from **50.632 ms** (`SCAN p`, full table scan) to **1.011 ms** (`SEARCH p USING INDEX`), achieving a **$50.1\times$ speedup** (`outputs/reports/c1_experiment_results.txt`).
  * The tiny feed ranker scored and ranked candidates in **4.268 ms**.
* **C2 — GitHub Actions CI & Code Review:**
  * Automated workflow (`.github/workflows/ci.yml`) runs linting and pytest on push and pull requests.
  * Includes standardized PR template (`.github/pull_request_template.md`) and branch protection merge checklist.
* **C3 — System Design Theory:**
  * Glossary of 10 core architectural terms with concrete real-world examples.
  * In-depth trade-off analysis of Strong Consistency vs. High Availability under CAP/PACELC.
* **C4 — System Design Workflow:**
  * 5-step repeatable system design sequence.
  * 1-page complete architecture document for a Scalable URL Shortener (TinyURL) handling 100M writes/month and 10B reads/month.

---

## 6. Verification & Test Suite

All 25 unit tests pass cleanly:
```bash
python -m pytest tests/ -v
```

```text
tests/test_cleaning.py::test_fix_datetime_types PASSED                   [  4%]
tests/test_cleaning.py::test_standardize_categories PASSED               [  8%]
tests/test_cleaning.py::test_handle_duplicates PASSED                    [ 12%]
tests/test_cleaning.py::test_process_resolution_durations PASSED         [ 16%]
tests/test_cleaning.py::test_handle_outliers PASSED                      [ 20%]
tests/test_cleaning.py::test_clean_dataset_end_to_end PASSED             [ 24%]
tests/test_features.py::test_add_engineered_features PASSED              [ 28%]
tests/test_features.py::test_generate_pandas_summaries PASSED            [ 32%]
tests/test_model.py::test_preprocessing_pipeline PASSED                  [ 36%]
tests/test_model.py::test_complaint_type_median_baseline PASSED          [ 40%]
tests/test_model.py::test_evaluate_predictions_metrics PASSED            [ 44%]
tests/test_model.py::test_validate_input_schema_success PASSED           [ 48%]
tests/test_model.py::test_validate_input_schema_missing_column PASSED    [ 52%]
tests/test_model.py::test_saved_pipeline_scoring_unseen_rows PASSED      [ 56%]
tests/test_validation.py::test_validate_uniqueness_pass PASSED           [ 60%]
tests/test_validation.py::test_validate_uniqueness_fail PASSED           [ 64%]
tests/test_validation.py::test_validate_types_pass PASSED                [ 68%]
tests/test_validation.py::test_validate_types_fail PASSED                [ 72%]
tests/test_validation.py::test_validate_null_constraints_pass PASSED     [ 76%]
tests/test_validation.py::test_validate_null_constraints_fail PASSED     [ 80%]
tests/test_validation.py::test_validate_ranges_pass PASSED               [ 84%]
tests/test_validation.py::test_validate_ranges_negative_duration PASSED  [ 88%]
tests/test_validation.py::test_validate_ranges_bad_coordinates PASSED    [ 92%]
tests/test_validation.py::test_quality_gate_passes_on_valid_data PASSED  [ 96%]
tests/test_validation.py::test_quality_gate_fails_loudly_on_corrupted_data PASSED [100%]
======================= 25 passed in 13.93s =======================
```

---

## 7. Checkpoints Completed

- [x] **Checkpoint 0 (17 Nov 2026):** Proposal approved (NYC 311 2010–2019 dataset, 20,000 stratified multi-year rows, target defined as continuous regression `resolution_hours`, open license documented).
- [x] **Checkpoint 1 (17 Nov 2026):** Raw data ingested, schema documented in `docs/schema.md`, repository structured.
- [x] **Checkpoint 2 (18 Nov 2026):** Modular cleaning functions with docstrings & type hints; negative durations separated to `rejected_rows.csv`; unit tests passing; NumPy vectorized ops & Pandas summaries generated.
- [x] **Checkpoint 3 (20 Nov 2026):** Visualizations rendered, SQLite demographic relational query executed and explained, before-and-after Data Quality Report completed, Part A 100% reproducible via single command.
- [x] **Checkpoint 4 (22 Nov 2026):** Problem framing, time-based split (train 2010–2017 vs test 2018–2019), leakage-free `ColumnTransformer` preprocessing pipeline.
- [x] **Checkpoint 5 (23 Nov 2026):** Model comparison (Complaint-median baseline vs Ridge vs HistGradientBoosting), cross-validation, subgroup residual error analysis.
- [x] **Checkpoint 6 (24 Nov 2026):** Serialized pipeline (`models/pipeline.joblib`), CLI inference script (`src/predict.py`), Part C systems exploration write-ups and artifacts (`src/exploration_c1.py`, `.github/workflows/ci.yml`, `docs/exploration.md`).
