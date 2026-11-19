# NYC 311 Service Requests: Raw Data Schema & Data Dictionary
**Dataset Identifier:** NYC Open Data `76ig-c548`
**Source URL:** [https://data.cityofnewyork.us/resource/76ig-c548.csv](https://data.cityofnewyork.us/resource/76ig-c548.csv)
**Access Date:** November 19, 2026
**Licence:** Open Public Government Data (NYC Terms of Use / Public Domain for Educational Research)
**Total Records:** 7,500 rows
**Total Fields:** 44 columns

---
## 1. Schema Overview & Data Dictionary

| Column Name | Inferred Dtype | Units / Domain | Missing Count | Missing % | Description / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `unique_key` | `int64` | Positive integer ID | 0 | 0.0% | Primary key assigned to each 311 request |
| `created_date` | `str` | YYYY-MM-DDTHH:MM:SS | 0 | 0.0% | Timestamp when the service request was lodged |
| `closed_date` | `str` | YYYY-MM-DDTHH:MM:SS | 111 | 1.5% | Timestamp when the agency marked request resolved |
| `agency` | `str` | 2-5 character acronym | 0 | 0.0% | City agency assigned (e.g. NYPD, HPD, DSNY, DOT) |
| `agency_name` | `str` | Full agency name | 0 | 0.0% | Full departmental title of responding entity |
| `complaint_type` | `str` | Predefined category | 0 | 0.0% | First-level classification (e.g. HEAT/HOT WATER) |
| `descriptor` | `str` | Specific issue detail | 109 | 1.5% | Sub-classification of the complaint |
| `descriptor_2` | `str` | Internal agency code | 4,305 | 57.4% | Secondary internal tracking descriptor |
| `location_type` | `str` | Location category | 1,691 | 22.5% | Property type (e.g. Residential Building, Street) |
| `incident_zip` | `float64` | 5-digit US Zipcode | 180 | 2.4% | Postal code of the incident location |
| `incident_address` | `str` | Street address | 457 | 6.1% | House number and street name |
| `street_name` | `str` | Street name | 458 | 6.1% | Name of street where incident occurred |
| `cross_street_1` | `str` | Street name | 3,090 | 41.2% | First intersecting street |
| `cross_street_2` | `str` | Street name | 3,092 | 41.2% | Second intersecting street |
| `intersection_street_1` | `str` | Street name | 4,122 | 55.0% | Primary street at nearest intersection |
| `intersection_street_2` | `str` | Street name | 4,120 | 54.9% | Cross street at nearest intersection |
| `address_type` | `str` | Address classification | 2,764 | 36.9% | Type of location address (ADDRESS, INTERSECTION) |
| `city` | `str` | City / Borough name | 361 | 4.8% | Town or city designation within NYC |
| `landmark` | `str` | Landmark name | 4,761 | 63.5% | Nearby recognized landmark or venue |
| `facility_type` | `str` | Facility category | 7,306 | 97.4% | Type of municipal facility involved |
| `status` | `str` | Closed, Open, Pending, etc. | 0 | 0.0% | Operational lifecycle state of the service ticket |
| `due_date` | `str` | YYYY-MM-DDTHH:MM:SS | 7,389 | 98.5% | Scheduled SLA deadline for response |
| `resolution_description` | `str` | Free text explanation | 607 | 8.1% | Agency action summary when resolving ticket |
| `resolution_action_updated_date` | `str` | YYYY-MM-DDTHH:MM:SS | 8 | 0.1% | Date action log was last updated |
| `community_board` | `str` | District identifier | 4 | 0.1% | Community Board administrative district |
| `council_district` | `float64` | Integer 1-51 | 210 | 2.8% | NYC City Council legislative district |
| `police_precinct` | `str` | Precinct number | 0 | 0.0% | NYPD local precinct designation |
| `bbl` | `float64` | 10-digit Borough-Block-Lot | 833 | 11.1% | NYC Department of Finance property identifier |
| `borough` | `str` | 5 NYC Boroughs + Unspecified | 4 | 0.1% | Administrative borough of New York City |
| `x_coordinate_state_plane` | `float64` | State Plane Long Island | 213 | 2.8% | NY State Plane X spatial coordinate |
| `y_coordinate_state_plane` | `float64` | State Plane Long Island | 213 | 2.8% | NY State Plane Y spatial coordinate |
| `open_data_channel_type` | `str` | PHONE, ONLINE, MOBILE, OTHER | 0 | 0.0% | Intake channel through which citizen contacted 311 |
| `park_facility_name` | `str` | Park or public facility name | 0 | 0.0% | Name of NYC Parks property |
| `park_borough` | `str` | 5 NYC Boroughs | 4 | 0.1% | Borough associated with park property |
| `vehicle_type` | `str` | Vehicle classification | 7,497 | 100.0% | Type of vehicle involved in TLC/traffic request |
| `taxi_company_borough` | `str` | 5 NYC Boroughs | 7,494 | 99.9% | Borough of licensed for-hire vehicle base |
| `taxi_pick_up_location` | `str` | Location string | 7,404 | 98.7% | Location of taxi pickup |
| `bridge_highway_name` | `str` | Highway / bridge name | 7,489 | 99.9% | Name of roadway structure |
| `bridge_highway_direction` | `str` | Direction code (NB, SB, EB, WB) | 7,489 | 99.9% | Traffic flow direction |
| `road_ramp` | `str` | Roadway vs Ramp | 7,489 | 99.9% | Classification of highway connector |
| `bridge_highway_segment` | `str` | Segment identifier | 7,489 | 99.9% | Specific mile marker or segment description |
| `latitude` | `float64` | 40.4° to 40.95° N | 213 | 2.8% | WGS84 Latitude geographic coordinate |
| `longitude` | `float64` | -74.3° to -73.65° W | 213 | 2.8% | WGS84 Longitude geographic coordinate |
| `location` | `str` | POINT (lon lat) | 213 | 2.8% | Well-Known Text geometry representation |

---
## 2. Measurable Data Quality Issues in Raw Ingestion

The raw operational data exhibits concrete, measurable quality anomalies that must be handled by the cleaning pipeline:

1. **Negative Operational Durations:** 61 records exhibit `closed_date < created_date` (e.g. closed hours or days before ticket was logged), indicating field logging errors.
2. **Missing Closed Dates (Right-Censored / Active Tickets):** 111 records have null `closed_date` because the request was still Open, Pending, or In-Progress at collection time.
3. **Invalid & Unspecified Borough Categorization:** 31 records contain `'Unspecified'` and 4 records contain `NaN` in the `borough` column.
4. **Missing Spatial Attributes:** 213 records (2.8%) lack valid `latitude`, `longitude`, and spatial coordinates.
5. **Extreme Duration Outliers:** Legitimate closed tickets span up to 47,261 hours (~5.4 years) due to backlog clearance of historic tickets.
6. **Type Inconsistencies:** `incident_zip` is stored as floating-point numbers (`11411.0`) with trailing decimals and missing values.
7. **Sparse Optional Fields:** Highway, taxi, and facility columns (e.g. `facility_type`, `vehicle_type`, `bridge_highway_name`) contain > 95% missing values as they only apply to specialized incident types.

---
## 3. Target Variable Definition for Tabular ML (Part B)

- **Target Name:** `is_long_resolution`
- **Type:** Binary Classification (`0`: Fast / Standard resolution within 24 hours, `1`: Long resolution taking > 24 hours)
- **Class Distribution:** Approximately 50.4% positive (`1`) vs 49.6% negative (`0`), providing a balanced classification benchmark.
- **Data Leakage Safeguard:** Columns created after ticket intake (`closed_date`, `resolution_description`, `resolution_action_updated_date`, `status`, `due_date`) must be strictly excluded from model feature sets.
