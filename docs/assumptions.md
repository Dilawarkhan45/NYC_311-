# Project Assumptions, Limitations & Data Quality Audit

**Project:** Reproducible Data Pipelines, Tabular ML & Systems Exploration  
**Dataset:** NYC 311 Service Requests (`76ig-c548`)  
**Author:** Warisha / Data Engineering Student  
**Roll Number:** 2026-DS-0142  
**Date:** November 19, 2026  

---

## 1. Checkpoint 0: Dataset Proposal & Problem Context

- **Data Source:** Official City of New York Open Data SODA API endpoint ([`https://data.cityofnewyork.us/resource/76ig-c548.csv`](https://data.cityofnewyork.us/resource/76ig-c548.csv)).
- **Volume & Dimensions:** Ingested 7,500 raw rows and 44 columns, surpassing the mandatory minimums of 5,000 rows and 8 columns.
- **Operational Origin:** Real-world municipal non-emergency service request logs managed by the NYC Department of Information Technology and Telecommunications (DoITT).
- **Licence & Terms:** Open Public Government Data under NYC Open Data Terms of Use (public domain for academic and analytical research).
- **Target Selection:** `is_long_resolution` — A binary operational indicator indicating whether a service request takes longer than 24.0 hours to resolve.
- **Intended Operational Purpose:** Enables city dispatch managers, call center operators, and municipal agencies (NYPD, HPD, DSNY, DOT) to triage incoming requests at ticket creation, proactively flagging cases likely to breach service-level agreements (SLAs).

---

## 2. Core Engineering Assumptions

1. **Chronological Validity:** An incident can never be authentically resolved before it is registered. Service requests exhibiting negative resolution durations (`closed_date < created_date`) represent logging artifacts or clock desynchronization and must be rejected from resolution analyses.
2. **Geographical Bounding:** Official New York City administrative responsibilities reside within coordinates between Latitude 40.48°N - 40.95°N and Longitude -74.30°W - -73.65°W. Any incident recorded outside this bounding polygon cannot be serviced by NYC agencies.
3. **Borough Integrity:** Service tickets marked as `'Unspecified'` or null borough lack jurisdictional routing and are pruned from borough-level performance benchmarks.
4. **Target Leakage Safeguard:** In predicting whether a ticket will take >24 hours to resolve, only information available at intake (intake channel, complaint type, borough, incident coordinates, time of day, day of week) can be used. All resolution-dependent columns (`closed_date`, `resolution_description`, `resolution_action_updated_date`, `status`, `due_date`) are strictly isolated and excluded from model features.

---

## 3. Deliberate Cleaning Decisions: What We Chose NOT to Fix & Why

| Dimension / Column | Observed State | Decision | Architectural & Domain Justification |
| :--- | :--- | :--- | :--- |
| **Physical Landmarks & Highway Segments** (`landmark`, `bridge_highway_name`) | >60% to 95% missing values | **Retained as missing / un-imputed** | Synthetically imputing physical landmarks or bridge segments would fabricate fictitious geography. These columns are only populated when incidents occur on specialized infrastructure. |
| **Open / In-Progress Tickets** (`closed_date` is null) | 111 tickets still pending resolution | **Retained in cleaned master table; filtered for resolution duration target** | Active cases represent ongoing municipal operations. They are kept for operational inventory analysis, but filtered when calculating historical duration metrics and ML target training. |
| **Extreme Resolution Durations** (up to 47,261 hours / ~5.4 years) | Long-tail outlier durations from historical backlog audits | **Capped at 8,760 hours (1 year) rather than deleted** | Deleting extreme cases would induce survival bias by ignoring multi-month bureaucratic bottlenecks. Capping at 1 year retains the event count while curbing numerical instability in statistical aggregations. |
| **Spatial Coordinates Missingness** (213 records with null coordinates) | Null latitude / longitude values | **Retained with missing indicator for median imputation** | Many phone complaints provide street intersections without GPS hardware. Dropping these would disproportionately penalize low-income or elderly residents who contact 311 via landline phone. |

---

## 4. Limitations of the Dataset

1. **Reporting Bias & Digital Divide:** 311 data measures citizen complaints rather than ground-truth physical incidents. High-density residential neighborhoods with tech-literate populations report significantly higher volumes via the mobile app, whereas rural or underserved communities may rely on phone calls or under-report.
2. **Seasonal Variance:** This sample covers winter conditions (December 2019), leading to an over-representation of `HEAT/HOT WATER` complaints (~25% of total volume). Findings must be contextualized when generalizing to summer operations.
3. **Absence of Severity Score:** Raw 311 tickets do not record an internal severity score (e.g. life-safety hazard vs cosmetic sidewalk crack). Models must infer resolution risk strictly from categorical complaint descriptors and intake channels.

---

## 5. Data Quality Audit: Before vs. After Cleaning Metrics

| Quality Dimension | Raw Ingested Data | Cleaned Pipeline Output | Net Change / Engineering Outcome |
| :--- | :--- | :--- | :--- |
| **Row Count** | 7,500 | 7,404 | 96 corrupted / non-actionable rows rejected (1.28%) |
| **Total Missing Cells** | 69,578 (21.08%) | 62,357 (16.51%) | Pruned invalid rows; standardized core columns |
| **Primary Key Uniqueness** | 100% Unique (7,500 keys) | 100% Unique (7,404 keys) | Uniqueness strictly validated |
| **Negative Duration Records** | 61 corrupted rows | 0 rows | 100% purged invalid logging timestamps |
| **Unspecified / Invalid Boroughs** | 35 records | 0 records | Normalized strictly to 5 NYC boroughs |
| **Spatial Outlier Violations** | 0 coordinate violations | 0 coordinate violations | All remaining GPS points validated within NYC bounds |
| **Validation Pass Rate** | 86.8% | **100.00%** | Exceeds 95.0% Quality Gate Threshold |
