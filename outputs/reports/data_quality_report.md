# NYC 311 Data Quality & Ingestion Audit Report
**Audit Timestamp:** 2026-11-19 21:25:09
**Target Dataset:** NYC Open Data 311 Service Requests (`76ig-c548`)

## 1. Executive Quality Summary

| Metric Dimension | Raw Input Value | Cleaned Output Value | Net Change / Action |
| :--- | :--- | :--- | :--- |
| **Total Records** | 7,500 | 7,404 | -96 (1.28% rejected) |
| **Total Missing Values** | 99,402 (30.12%) | 97,844 (25.41%) | Significant reduction in core features |
| **Primary Key Duplicates** | 0 | 0 | Strict 100% uniqueness enforced |
| **Negative Durations** | 61 | 0 | Invalid chronological errors purged |
| **Unspecified Boroughs** | 31 | 0 | Standardized to valid NYC boroughs |
| **Quality Gate Pass Rate** | 100.00% | 100.00% | Exceeds 95.0% SLA Threshold |

## 2. Field-Level Missingness Audit (Core Features)

| Field Name | Raw Missing % | Cleaned Missing % | Treatment Strategy |
| :--- | :--- | :--- | :--- |
| `unique_key` | 0.00% | 0.00% | Required / No nulls allowed |
| `created_date` | 0.00% | 0.00% | Required / No nulls allowed |
| `closed_date` | 1.48% | 1.50% | Retained / Handled in pipeline |
| `agency` | 0.00% | 0.00% | Retained / Handled in pipeline |
| `complaint_type` | 0.00% | 0.00% | Required / No nulls allowed |
| `borough` | 0.05% | 0.00% | Required / No nulls allowed |
| `latitude` | 2.84% | 1.89% | Retained / Handled in pipeline |
| `longitude` | 2.84% | 1.89% | Retained / Handled in pipeline |
| `incident_zip` | 2.40% | 1.45% | Retained / Handled in pipeline |

## 3. Assumptions and Cleaning Decisions
- **Chronological Integrity:** Records where resolution occurred prior to ticket creation are treated as corrupted data entry and excluded.
- **Borough Boundary Enforcement:** Non-NYC locations or unassigned boroughs ('Unspecified') cannot be routed to local municipal services and are pruned.
- **Duration Capping:** Durations greater than 8,760 hours (1 year) are capped to prevent distortion of summary means while retaining ticket frequency.
- **Imputation Philosophy:** Spatial coordinates are preserved with missing indicators for tabular imputation rather than indiscriminate row dropping.