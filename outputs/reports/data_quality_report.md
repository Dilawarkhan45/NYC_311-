# NYC 311 Service Requests: Data Quality & Audit Report (Part A)

**Author:** Dilawar khan  
**Roll Number:** TRN-2026-000961  
**Date:** 17 Nov 2026  
**Dataset:** NYC Open Data 311 Service Requests (`76ig-c548`)  
**Audit Execution Time:** 2026-11-21 23:25:05  

---

## 1. Executive Quality Summary (Before vs. After Cleaning)

| Problem / Dimension | Raw Ingested Count (%) | Cleaned Dataset Count (%) | Handling Strategy |
| :--- | :--- | :--- | :--- |
| **Total Records** | 20,000 (100.0%) | 17,502 (87.51%) | Pruned unserviceable/corrupted records |
| **Closed Before Created (Negative)** | 10 (0.050%) | 0 (0.00%) | Saved to `rejected_rows.csv` with reason |
| **Zero Duration Requests** | 375 (1.88%) | 364 (2.08%) | Kept and flagged with `is_zero_duration` |
| **Open Tickets (Missing closed_date)** | 517 (2.58%) | 392 (2.24%) | Reported as limitation; kept in cleaned master |
| **Unspecified / Missing Boroughs** | 2,488 (12.44%) | 0 (0.00%) | Filtered to enable jurisdictional analysis |
| **Sparse Location (Missing Lat/Lon)** | 435 (2.17%) | 365 (2.09%) | Preserved with missingness indicator |
| **Duplicate Primary Keys** | 0 (0.00%) | 0 (0.00%) | Uniqueness verified 100% |
| **Quality Gate Pass Rate** | 100.00% | 100.00% | Exceeds 95.0% SLA Threshold |

---

## 2. Missing Values Audit per Core Column

| Column Name | Raw Missing Count | Raw Missing % | Cleaned Missing Count | Cleaned Missing % | Treatment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `unique_key` | 0 | 0.00% | 0 | 0.00% | Zero nulls enforced |
| `created_date` | 0 | 0.00% | 0 | 0.00% | Zero nulls enforced |
| `closed_date` | 517 | 2.58% | 392 | 2.24% | Retained for downstream modeling |
| `agency` | 0 | 0.00% | 0 | 0.00% | Retained for downstream modeling |
| `complaint_type` | 0 | 0.00% | 0 | 0.00% | Zero nulls enforced |
| `borough` | 1 | 0.01% | 0 | 0.00% | Zero nulls enforced |
| `incident_zip` | 369 | 1.85% | 300 | 1.71% | Retained for downstream modeling |
| `latitude` | 435 | 2.17% | 365 | 2.09% | Retained for downstream modeling |
| `longitude` | 435 | 2.17% | 365 | 2.09% | Retained for downstream modeling |

---

## 3. Rejected Records Accounting
- **Rejected Count:** 10 records rejected due to negative duration timestamps.
- **Destination Artifact:** [`outputs/reports/rejected_rows.csv`](rejected_rows.csv)
- **Rejection Criterion:** Records where `closed_date < created_date` violate chronological reality and indicate data entry error.

---

## 4. Key Limitations & Assumptions
1. **Right-Censored Active Tickets:** Open requests lack completion timestamps. Removing them from regression training can bias model towards faster resolution, which is documented as a model limitation.
2. **Severe Right Skew:** Resolution times span from minutes to multi-year backlogs; log(1 + hours) is applied to ensure numerical stability.
3. **Reporting Disparities:** Digital divide across boroughs affects mobile app usage vs phone hotlines.