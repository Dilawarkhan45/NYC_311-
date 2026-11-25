# NYC 311 Data Quality, ML, and Systems Exploration

An end-to-end Python project that ingests NYC 311 service requests, produces a validated and enriched dataset, predicts resolution time, and explores database indexing and systems-design concepts.

**Data source:** [NYC 311 Service Requests from 2010 to 2019](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-2019/76ig-c548)

---

## Project overview

The repository has three deliverables:

- **Part A - Data pipeline:** Download a stratified 2010-2019 sample, clean and validate records, engineer features, generate reports and visualizations, and load the data into SQLite.
- **Part B - Resolution-time regression:** Train and compare a complaint-type median baseline, Ridge regression, and HistGradientBoosting. Serialize the selected preprocessing and model pipeline for batch or single-record inference.
- **Part C - Systems exploration:** Benchmark SQLite feed queries, implement a small feed ranker, document GitHub Actions and code-review practices, and write system-design notes.

## Key outputs

- Cleaned, reproducible dataset: `data/cleaned/cleaned_311_data.csv`
- Untouched downloaded sample: `data/raw/raw_311_data.csv`
- Serialized inference pipeline: `models/pipeline.joblib`
- SQLite database: `data/nyc_311.db`
- Quality and model reports: `outputs/reports/`
- Analytical charts: `outputs/figures/`
- Schema and project assumptions: `docs/schema.md` and `docs/assumptions.md`
- Systems write-up: `docs/exploration.md`

## Repository structure

```text
NYC_311/
├── src/
│   ├── extract.py           # Stratified NYC Open Data extraction
│   ├── clean.py             # Cleaning and anomaly handling
│   ├── validate.py          # Constraints and quality gate
│   ├── features.py          # Feature engineering and summaries
│   ├── visualize.py         # Matplotlib/Seaborn visualizations
│   ├── database.py          # SQLite loading and demographic joins
│   ├── run_pipeline.py      # Complete Part A pipeline
│   ├── train.py             # Part B model training
│   ├── predict.py           # Batch and single-record inference
│   └── exploration_c1.py    # SQLite index and feed-ranker benchmark
├── tests/                   # Pytest unit tests
├── data/
│   ├── raw/
│   ├── cleaned/
│   └── nyc_311.db
├── models/
├── outputs/
│   ├── figures/
│   └── reports/
├── docs/
├── sql/
├── notebooks/
└── requirements.txt
```

## Requirements

- Python 3.10 or newer
- Internet access for an initial download of the NYC Open Data sample
- The dependencies listed in `requirements.txt`

The dependencies include pandas, NumPy, scikit-learn, joblib, Matplotlib, Seaborn, Requests, and pytest.

## Setup

From the repository root:

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The extraction module uses an existing raw dataset and skips the API download when it already contains at least 20,000 rows spanning the expected years. Pass `--force` to `run_pipeline.py` to re-download it.

## Running the project

### 1. Build the data pipeline

```bash
python src/run_pipeline.py
```

For a forced API refresh:

```bash
python src/run_pipeline.py --force
```

This pipeline:

1. Reads or downloads the stratified raw sample.
2. Removes duplicate keys and records with invalid timestamps.
3. Adds temporal and geographic features.
4. Validates uniqueness, types, null constraints, ranges, and coordinates.
5. Enforces a 95% validation pass-rate quality gate.
6. Writes the cleaned dataset, reports, charts, and SQLite database.

The raw data remains unchanged; negative-duration records are written to `outputs/reports/rejected_rows.csv`.

### 2. Train the regression models

```bash
python src/train.py
```

Training uses closed tickets only and splits by creation year:

- Training: 2010-2017
- Testing: 2018-2019

The script performs expanding time-window cross-validation, evaluates the baseline and learned models, saves subgroup error reports and charts, and writes `models/pipeline.joblib`.

### 3. Run batch inference

```bash
python src/predict.py ^
  --input data/cleaned/cleaned_311_data.csv ^
  --output outputs/reports/predictions.csv
```

Use PowerShell-style line continuation instead when running from PowerShell:

```powershell
python src/predict.py `
  --input data/cleaned/cleaned_311_data.csv `
  --output outputs/reports/predictions.csv
```

The script requires the feature columns documented in `src/predict.py`. It adds derived temporal and distance features when a `created_date` and coordinates are supplied. The output contains `predicted_resolution_hours` and `predicted_resolution_days`.

### 4. Run single-record inference

```bash
python src/predict.py ^
  --agency NYPD ^
  --complaint "Noise - Residential" ^
  --borough MANHATTAN ^
  --channel PHONE ^
  --lat 40.7128 ^
  --lon -74.0060 ^
  --hour 12 ^
  --day 0
```

Run `python src/predict.py --help` for the complete CLI options.

### 5. Run the systems benchmark

```bash
python src/exploration_c1.py
```

This creates a synthetic SQLite feed dataset, compares plans and timings with and without the composite post index, and writes `outputs/reports/c1_experiment_results.txt`.

### 6. Run the tests

```bash
python -m pytest tests/ -v
```

The suite covers cleaning, feature engineering, validation and quality-gate behavior, preprocessing, model baselines, metrics, input schema validation, and saved-pipeline inference.

## Data quality summary

The current cleaned artifact contains 17,502 records and satisfies the 95% quality gate. The audit log reports:

- 0 duplicate primary keys
- 0 negative-duration violations
- 0 out-of-bounds coordinate violations
- 392 open tickets retained in the cleaned master dataset

Open tickets are retained for inventory analysis but excluded from resolution-time modeling because their close dates are unavailable.

The raw and cleaned quality reports are available at:

- `outputs/reports/quality_report.md`
- `outputs/reports/data_quality_report.md`
- `outputs/reports/metrics.json`

## Machine-learning approach

Only information available at intake is used as a predictor. Resolution-dependent fields such as `closed_date`, `status`, and resolution description columns are excluded.

Predictors include:

- Agency
- Complaint type
- Borough
- Intake channel
- Intake hour
- Day of week
- Weekend indicator
- Latitude and longitude
- Haversine distance from NYC City Hall

Numeric features use median imputation and scaling. Categorical features use mode imputation and one-hot encoding. Ridge and HistGradientBoosting models train on `log1p(resolution_hours)` and are evaluated after converting predictions back to hours.

The latest generated model-comparison report is shown below:

| Model | Test MAE | Test RMSE | Test R² |
|---|---:|---:|---:|
| Complaint-type median baseline | 374.31 hours | 1,441.08 hours | 0.2035 |
| Ridge regression (`log1p`) | 382.27 hours | 1,593.20 hours | 0.0265 |
| HistGradientBoosting (`log1p`) | 386.80 hours | 1,609.16 hours | 0.0069 |

The baseline is stronger on this test split than the two more complex regressors. The result is not evidence of an optimal production model, only of the current feature set and temporal evaluation.

See `outputs/reports/model_comparison.csv` and `outputs/reports/borough_model_error.csv` for the complete generated metrics.

## Systems findings

The synthetic C1 benchmark compares feed retrieval with 50,000 posts and 5,000 follow relationships. A composite `(author_id, created_at DESC)` index changed the query plan from a table scan and temporary sort to indexed seeks.

The generated experiment report is at `outputs/reports/c1_experiment_results.txt`. The latest benchmark is documented in `docs/exploration.md`, together with:

- Fan-out-on-read and fan-out-on-write trade-offs
- GitHub Actions CI
- Pull-request and code-review practices
- Architecture glossary
- A URL-shortener system design

## Documentation

- [Data schema](docs/schema.md)
- [Assumptions and model card](docs/assumptions.md)
- [Systems exploration](docs/exploration.md)
- [SQL queries](sql/queries.sql)
- [Interactive notebook](notebooks/exploration.ipynb)
- [GitHub Actions workflow](.github/workflows/ci.yml)

## Reproducibility and limitations

- The API extraction uses deterministic offsets and fixed random ordering seeds.
- The pipeline persists both raw and cleaned data artifacts.
- Running against a newly downloaded sample can change row counts and metrics if the source API has changed or recent rows are unavailable.
- Resolution times are strongly skewed and affected by right-censored open cases.
- Resolution outcomes may reflect historical reporting and operational policies, not true incident severity or equitable service quality.
- The model should not be used for emergency dispatch or individual performance evaluation.

## Data usage

The source dataset is provided by NYC Open Data under its published terms of use. A local copy in `data/raw/` is retained for deterministic project execution and should be handled according to those terms.
