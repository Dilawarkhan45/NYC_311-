# NYC 311 Service Requests: Raw Data Schema & Data Dictionary

**Author:** Dilawar khan  
**Roll Number:** TRN-2026-000961  
**Date:** 17 Nov 2026  
**Dataset Identifier:** NYC Open Data `76ig-c548`  
**Dataset Title:** NYC 311 Service Requests from 2010 to 2019  
**Source URL:** [https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-2019/76ig-c548/about_data](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-2019/76ig-c548/about_data)  
**Publisher:** NYC311 / Office of Technology and Innovation (OTI), NYC Open Data  
**Licence:** Public use under NYC Open Data Terms of Use (Public Domain for Educational/Academic Research)  
**Sample Specification:** 20,000 rows × 44 columns (Stratified time-based sample: 2,000 requests per year across 2010 to 2019, ~167 per month, fixed random seed)  

---

## 1. Schema Overview & Data Dictionary

| Column Name | Inferred Dtype | Units / Domain | Missing Count | Missing % | Description & Domain Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `unique_key` | Integer | Positive integer ID | 0 | 0.00% | Primary key assigned to each 311 service request |
| `created_date` | Datetime (ISO) | YYYY-MM-DDTHH:MM:SS | 0 | 0.00% | Timestamp when request was officially registered |
| `closed_date` | Datetime (ISO) | YYYY-MM-DDTHH:MM:SS | 517 | 2.59% | Timestamp when agency resolved or closed ticket (NaN = Still Open) |
| `agency` | Categorical | 2-5 character code | 0 | 0.00% | Responding NYC department (NYPD, HPD, DOT, DSNY, DEP, etc.) |
| `agency_name` | Text | Department title | 0 | 0.00% | Full departmental designation of the responding agency |
| `complaint_type` | Categorical | Municipal category | 0 | 0.00% | First-level classification of citizen problem |
| `descriptor` | Categorical | Specific subcategory | 358 | 1.79% | Detailed issue description |
| `descriptor_2` | Categorical | Internal code | 11,884 | 59.42% | Secondary internal agency tracking code |
| `location_type` | Categorical | Property classification | 4,284 | 21.42% | Type of property (e.g. Residential Building, Street, Sidewalk) |
| `incident_zip` | Categorical | 5-digit US Postal Code | 572 | 2.86% | Postal zip code of the reported incident |
| `incident_address` | Text | Street address | 1,220 | 6.10% | Number and street name where incident occurred |
| `street_name` | Text | Street name | 1,224 | 6.12% | Street name of the complaint site |
| `cross_street_1` | Text | Street name | 7,651 | 38.26% | First intersecting cross street |
| `cross_street_2` | Text | Street name | 7,660 | 38.30% | Second intersecting cross street |
| `intersection_street_1` | Text | Street name | 10,812 | 54.06% | First street for intersection reporting |
| `intersection_street_2` | Text | Street name | 10,808 | 54.04% | Second street for intersection reporting |
| `address_type` | Categorical | Address classification | 6,838 | 34.19% | Address type (ADDRESS, INTERSECTION, LATLONG, BLOCKFACE) |
| `city` | Categorical | NYC City / Town name | 1,024 | 5.12% | Locality or borough town name |
| `landmark` | Text | Landmark name | 12,984 | 64.92% | Recognized NYC public facility or venue |
| `facility_type` | Categorical | Facility category | 19,410 | 97.05% | Type of municipal facility involved |
| `status` | Categorical | Lifecycle state | 0 | 0.00% | Operational state (Closed, Pending, Open, In Progress) |
| `due_date` | Datetime (ISO) | YYYY-MM-DDTHH:MM:SS | 19,650 | 98.25% | Scheduled SLA resolution deadline |
| `resolution_description` | Text | Free text summary | 462 | 2.31% | Written explanation of agency findings and action taken |
| `resolution_action_updated_date` | Datetime (ISO) | YYYY-MM-DDTHH:MM:SS | 382 | 1.91% | Timestamp when resolution status was last updated |
| `community_board` | Categorical | Community district | 0 | 0.00% | Administrative community district identifier |
| `council_district` | Numeric | Integer 1 - 51 | 845 | 4.23% | NYC City Council legislative district |
| `police_precinct` | Categorical | Precinct number | 843 | 4.22% | NYPD precinct jurisdiction |
| `bbl` | Numeric | 10-digit ID | 2,145 | 10.72% | Borough-Block-Lot real property tax lot number |
| `borough` | Categorical | 5 NYC Boroughs | 2,488 | 12.44% | Administrative borough (BRONX, BROOKLYN, MANHATTAN, QUEENS, STATEN ISLAND) |
| `x_coordinate_state_plane` | Numeric (Feet) | NY Long Island Plane | 435 | 2.18% | Spatial X coordinate in feet |
| `y_coordinate_state_plane` | Numeric (Feet) | NY Long Island Plane | 435 | 2.18% | Spatial Y coordinate in feet |
| `open_data_channel_type` | Categorical | Channel name | 0 | 0.00% | Intake channel (PHONE, ONLINE, MOBILE, OTHER) |
| `park_facility_name` | Text | Park name | 0 | 0.00% | NYC Parks property name (default: "Unspecified") |
| `park_borough` | Categorical | 5 NYC Boroughs | 0 | 0.00% | Borough responsible for park property |
| `vehicle_type` | Categorical | Vehicle class | 19,944 | 99.72% | Commercial vehicle type (TLC/Taxi requests) |
| `taxi_company_borough` | Categorical | 5 NYC Boroughs | 19,956 | 99.78% | Borough of licensed taxi company |
| `taxi_pick_up_location` | Text | Location | 19,928 | 99.64% | Taxi passenger pickup location |
| `bridge_highway_name` | Text | Infrastructure name | 19,892 | 99.46% | Name of highway or bridge |
| `bridge_highway_direction` | Categorical | Direction code | 19,895 | 99.48% | Direction of traffic flow (e.g. NB, SB) |
| `road_ramp` | Categorical | Roadway vs Ramp | 19,895 | 99.48% | Roadway connector classification |
| `bridge_highway_segment` | Text | Segment ID | 19,880 | 99.40% | Mile marker or highway segment |
| `latitude` | Float (Degrees) | 40.48° to 40.95° N | 435 | 2.18% | WGS84 geographic latitude |
| `longitude` | Float (Degrees) | -74.30° to -73.65° W | 435 | 2.18% | WGS84 geographic longitude |
| `location` | WKT Point | POINT (lon lat) | 435 | 2.18% | GeoJSON / WKT spatial point |

---

## 2. Measurable Operational Data Quality Problems

The 20,000 raw operational records exhibit concrete, measurable anomalies:
1. **Requests Closed Before Created:** 10 records exhibit `closed_date < created_date` (negative duration logging errors). These are isolated and saved to `outputs/reports/rejected_rows.csv` with the rejection reason.
2. **Missing Closed Dates (Open Tickets):** 517 requests (2.59%) are actively pending resolution with null `closed_date`.
3. **Zero Duration Tickets:** 375 records (1.88%) have `closed_date == created_date` (0.0 hours), representing immediate resolutions or automated closures. These are retained and flagged.
4. **Unspecified / Missing Boroughs:** 2,488 records (12.44%) lack a valid borough designation, preventing jurisdictional allocation.
5. **Sparse Coordinates:** 435 records (2.18%) lack latitude and longitude.
6. **Extreme Right Skew:** Resolution durations extend up to 79,087.6 hours (~9 years), justifying `log(1 + resolution_hours)` transformation.

---

## 3. Target Variable Specification for Regression

- **Target Column:** `resolution_hours = (closed_date - created_date).total_seconds() / 3600.0`
- **Target Type:** Continuous numerical (regression, measured in hours).
- **Transformation:** `log_resolution_hours = np.log1p(resolution_hours)` for modeling right-skewed durations.
- **Leakage Prevention:** Features are strictly limited to information known at intake time: `complaint_type`, `descriptor`, `agency`, `borough`, `open_data_channel_type`, `latitude`, `longitude`, `created_hour`, `created_day_of_week`, `is_weekend`. Resolution-dependent attributes (`closed_date`, `status`, `resolution_description`, `resolution_action_updated_date`, `due_date`) are strictly isolated.
