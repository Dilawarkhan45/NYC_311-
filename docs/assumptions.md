# Project Assumptions, Limitations & Machine Learning Model Card

**Author:** Dilawar khan  
**Roll Number:** TRN-2026-000961  
**Date:** 17 Nov 2026  
**Course Project:** Reproducible Data Pipelines, Tabular ML & Systems Exploration  
**Dataset:** NYC 311 Service Requests from 2010 to 2019 (`76ig-c548`)  

---

## 1. Checkpoint 0: Dataset Proposal Summary

- **Source & Publisher:** NYC Open Data (Socrata), published by NYC311 and maintained by the Office of Technology and Innovation (OTI). Endpoint: [`https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-2019/76ig-c548/about_data`](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-2019/76ig-c548/about_data)
- **Licence:** Open Public Government Data under NYC Open Data Terms of Use (Public Domain for educational and research usage).
- **Size and Scope:** The complete dataset contains 22.6M rows and 44 columns. A reproducible stratified sample of **20,000 rows** was collected across all ten years (2010 to 2019): exactly 2,000 requests per year, spread over all 12 months (~167 per month), using fixed random seeds.
- **Problem Formulation:** Regression task predicting `resolution_hours = closed_date - created_date` (in hours) using information available at ticket creation time.
- **Target Transformation:** Because resolution durations are strongly right-skewed (spanning from minutes to multiple years), modeling utilizes $\log(1 + \text{hours})$, and errors are reported back in hours (MAE, RMSE, $R^2$).

---

## 2. Core Operational Assumptions

1. **Chronological Consistency:** In an operational municipal ticketing system, resolution cannot occur before ticket intake. Records with `closed_date < created_date` are logging errors and must be saved to a rejected records log (`outputs/reports/rejected_rows.csv`) with the rejection reason.
2. **Immediate Closures (Zero Durations):** Tickets with `resolution_hours == 0.0` (375 records in our sample) represent instantaneous operational responses (e.g. automated referrals or immediate on-site inspection closures). These are kept in the dataset and flagged with `is_zero_duration = True`.
3. **Open Tickets (Right-Censored Data):** Tickets missing `closed_date` (517 records) are currently open or in progress. They are preserved in the cleaned master dataset for operational inventory analysis, but excluded when computing historical resolution metrics and target training.
4. **Geographic Boundaries:** Valid New York City service locations fall within the bounding box of Latitude 40.48°N to 40.95°N and Longitude -74.30°W to -73.65°W.
5. **Data Leakage Safeguards:** Only features known at intake time (`agency`, `complaint_type`, `descriptor`, `borough`, `open_data_channel_type`, `latitude`, `longitude`, `created_hour`, `created_day_of_week`, `is_weekend`) may be utilized. All resolution-dependent columns (`closed_date`, `status`, `resolution_description`, `resolution_action_updated_date`, `due_date`) are strictly isolated.

---

## 3. Deliberate Decisions: What We Chose NOT to Fix & Why

| Column / Condition | Observed State | Decision | Domain Justification |
| :--- | :--- | :--- | :--- |
| **Physical Landmarks & Highway Segments** (`landmark`, `bridge_highway_name`) | >60% to 99% missing values | **Retained as missing without imputation** | Imputing fictitious bridge or highway names on residential streets distorts spatial reality. These fields only apply to specialized incident classes. |
| **Open Requests** (`closed_date` is null) | 517 active requests | **Retained in master table; reported as open** | Deleting active tickets from the master inventory introduces survival bias (slow requests take longer to close). They are flagged and separated during duration modeling. |
| **Extreme Outliers** (up to 79,087.6 hours) | Historical backlog closures spanning multiple years | **Capped at 8,760 hours (1 year) and log-transformed** | Deleting backlogged cases discards real bureaucratic friction. Capping at 1 year and using $\log(1 + \text{hours})$ prevents numerical instability in aggregations. |
| **Spatial Coordinates Missingness** (435 null coordinates) | Null GPS coordinates | **Retained with missing indicator** | Citizens calling via landline hotlines frequently report cross-streets without GPS tags. Dropping them penalizes low-income or elderly populations. |

---

## 4. Limitations of the Dataset

1. **Reporting Bias & Digital Divide:** 311 records measure civic complaints rather than physical incident occurrences. Tech-enabled boroughs report heavily via mobile applications, while other neighborhoods rely on telephone hotlines.
2. **Right-Censoring of Slow Cases:** Excluding open tickets from regression models can bias predictions toward faster requests, as slow cases remain open longer.
3. **Absence of Intrinsic Severity Metrics:** The raw 311 feed lacks an objective priority score; urgency must be inferred from complaint type and channel.

---

## 5. Data Quality Audit: Before vs. After Cleaning Metrics

| Quality Dimension | Raw Ingested (20,000 rows) | Cleaned Master Dataset | Engineering Action / Finding |
| :--- | :--- | :--- | :--- |
| **Total Rows** | 20,000 (100.0%) | 17,502 (87.51%) | Pruned unserviceable borough rows |
| **Negative Durations** | 10 records (0.05%) | 0 records (0.00%) | Separated into `rejected_rows.csv` with reason |
| **Zero Duration Tickets** | 375 records (1.88%) | 375 records (2.14%) | Preserved and flagged with `is_zero_duration` |
| **Open Tickets (Null closed_date)** | 517 records (2.59%) | 517 records (2.95%) | Preserved in cleaned master for inventory |
| **Missing / Unspecified Boroughs** | 2,488 records (12.44%) | 0 records (0.00%) | Pruned to enforce municipal boundaries |
| **Missing Coordinates** | 435 records (2.18%) | 0 records (0.00%) | Preserved with missingness flags |
| **Quality Gate Pass Rate** | 85.3% | **100.00%** | Exceeds 95.0% Quality Gate threshold |

---

## 6. Part B Model Card: NYC 311 Resolution Time Regressor

### A. Intended Use
* **Primary Intended Use:** Predicts the estimated turnaround time (in hours and days) for incoming NYC 311 non-emergency service requests at the moment of intake.
* **Target Users:** NYC 311 Operations Dispatchers, City Agency Resource Coordinators (NYPD, HPD, DOT, DSNY, DEP), and civic dashboard systems.
* **Out-of-Scope Use:** The model is not designed for dispatching emergency 911 police/fire services or assessing individual municipal worker job performance.

### B. Factors & Feature Engineering
* **Categorical Predictors:** Responding agency (`agency`), complaint category (`complaint_type`), geographic borough (`borough`), intake channel (`open_data_channel_type`).
* **Continuous / Spatial Predictors:** Intake hour (`created_hour`), day of week (`created_day_of_week`), weekend flag (`is_weekend`), Haversine distance from NYC City Hall (`distance_to_center_km`), latitude, and longitude.
* **Leakage Exclusion:** Resolution-dependent attributes (`closed_date`, `status`, `resolution_description`, `resolution_action_updated_date`, `due_date`) are strictly isolated and omitted.

### C. Training & Evaluation Splits
* **Temporal Partitioning:**
  * **Training Split:** Requests registered from **2010 through 2017** ($13,175$ closed rows, $77.0\%$).
  * **Test Split:** Requests registered from **2018 through 2019** ($3,935$ closed rows, $23.0\%$).
* **Cross-Validation:** Expanding time-window cross-validation on the training set using `TimeSeriesSplit(n_splits=4)` to mimic real-world forward testing.

### D. Quantitative Performance Comparison
Models are trained on $\log(1 + \text{hours})$ and evaluated on back-transformed physical units (Hours):

| Model Architecture | CV MAE (Hours) | Test MAE (Hours) | Test RMSE (Hours) | Test $R^2$ | Pipeline Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (Complaint Median)** | N/A (Heuristic) | 374.31 hrs | 1,441.08 hrs | 0.2035 | Training median mapped per complaint type |
| **Ridge Regression ($\log 1p$)** | **319.12 hrs** | 382.27 hrs | 1,593.20 hrs | 0.0265 | `ColumnTransformer` + `Ridge(alpha=10.0)` |
| **HistGradientBoosting ($\log 1p$)** | **330.34 hrs** | 386.80 hrs | 1,609.16 hrs | 0.0069 | `ColumnTransformer` + `HistGradientBoosting` |

### E. Error Patterns & Concrete Failure Modes
1. **High-Residual Extreme Outliers:** In both Ridge and Gradient Boosting, tickets requiring multi-month investigations (e.g. chronic structural foundation disputes under DOB or illegal building conversions under HPD taking $>5,000$ hours) produce large positive residuals.
2. **Subgroup Disparities:** Manhattan exhibits the largest mean absolute error ($482.1$ hours), driven by high-density commercial/tenant disputes, whereas Staten Island exhibits the lowest error ($241.6$ hours) due to standardized sanitation and traffic service requests.
3. **Decisive Features:** Permutation feature importance confirms that `agency` and `complaint_type` account for over $65\%$ of predictive power, validating that departmental operational capacity dictates resolution time far more than geographic coordinates.

### F. Ethical Considerations & Operational Caveats
* **Geographic Equity:** Models trained on historical civic response times must not be used to justify under-resourcing historically slower neighborhoods. Proactive alert flags should trigger operational support rather than triage deprioritization.
* **Right-Censored Active Cases:** Because active tickets lack closed timestamps, they are excluded from duration modeling. This under-represents cases that experience prolonged bureaucratic delays.
