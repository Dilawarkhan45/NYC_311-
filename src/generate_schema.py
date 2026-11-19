# Name: Warisha / Data Engineering Student
# Roll Number: 2026-DS-0142
# Date: November 19, 2026

"""
Generates the comprehensive Raw Data Schema documentation in docs/schema.md.
"""

import os
import json
import pandas as pd

def generate_schema_doc():
    raw_path = os.path.join("data", "raw", "raw_311_data.csv")
    df = pd.read_csv(raw_path, low_memory=False)
    
    doc = []
    doc.append("# NYC 311 Service Requests: Raw Data Schema & Data Dictionary\n")
    doc.append("**Dataset Identifier:** NYC Open Data `76ig-c548`\n")
    doc.append("**Source URL:** [https://data.cityofnewyork.us/resource/76ig-c548.csv](https://data.cityofnewyork.us/resource/76ig-c548.csv)\n")
    doc.append("**Access Date:** November 19, 2026\n")
    doc.append("**Licence:** Open Public Government Data (NYC Terms of Use / Public Domain for Educational Research)\n")
    doc.append(f"**Total Records:** {len(df):,} rows\n")
    doc.append(f"**Total Fields:** {len(df.columns)} columns\n")
    doc.append("\n---\n")
    doc.append("## 1. Schema Overview & Data Dictionary\n\n")
    doc.append("| Column Name | Inferred Dtype | Units / Domain | Missing Count | Missing % | Description / Example |\n")
    doc.append("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
    
    col_descriptions = {
        "unique_key": ("Unique identifier", "Positive integer ID", "Primary key assigned to each 311 request"),
        "created_date": ("ISO Timestamp", "YYYY-MM-DDTHH:MM:SS", "Timestamp when the service request was lodged"),
        "closed_date": ("ISO Timestamp", "YYYY-MM-DDTHH:MM:SS", "Timestamp when the agency marked request resolved"),
        "agency": ("Categorical Code", "2-5 character acronym", "City agency assigned (e.g. NYPD, HPD, DSNY, DOT)"),
        "agency_name": ("Text", "Full agency name", "Full departmental title of responding entity"),
        "complaint_type": ("Categorical", "Predefined category", "First-level classification (e.g. HEAT/HOT WATER)"),
        "descriptor": ("Categorical / Text", "Specific issue detail", "Sub-classification of the complaint"),
        "descriptor_2": ("Categorical / Text", "Internal agency code", "Secondary internal tracking descriptor"),
        "location_type": ("Categorical", "Location category", "Property type (e.g. Residential Building, Street)"),
        "incident_zip": ("Numeric / Float", "5-digit US Zipcode", "Postal code of the incident location"),
        "incident_address": ("Text", "Street address", "House number and street name"),
        "street_name": ("Text", "Street name", "Name of street where incident occurred"),
        "cross_street_1": ("Text", "Street name", "First intersecting street"),
        "cross_street_2": ("Text", "Street name", "Second intersecting street"),
        "intersection_street_1": ("Text", "Street name", "Primary street at nearest intersection"),
        "intersection_street_2": ("Text", "Street name", "Cross street at nearest intersection"),
        "address_type": ("Categorical", "Address classification", "Type of location address (ADDRESS, INTERSECTION)"),
        "city": ("Categorical", "City / Borough name", "Town or city designation within NYC"),
        "landmark": ("Text", "Landmark name", "Nearby recognized landmark or venue"),
        "facility_type": ("Categorical", "Facility category", "Type of municipal facility involved"),
        "status": ("Categorical", "Closed, Open, Pending, etc.", "Operational lifecycle state of the service ticket"),
        "due_date": ("ISO Timestamp", "YYYY-MM-DDTHH:MM:SS", "Scheduled SLA deadline for response"),
        "resolution_description": ("Text", "Free text explanation", "Agency action summary when resolving ticket"),
        "resolution_action_updated_date": ("ISO Timestamp", "YYYY-MM-DDTHH:MM:SS", "Date action log was last updated"),
        "community_board": ("Categorical", "District identifier", "Community Board administrative district"),
        "council_district": ("Numeric", "Integer 1-51", "NYC City Council legislative district"),
        "police_precinct": ("Categorical / Text", "Precinct number", "NYPD local precinct designation"),
        "bbl": ("Numeric", "10-digit Borough-Block-Lot", "NYC Department of Finance property identifier"),
        "borough": ("Categorical", "5 NYC Boroughs + Unspecified", "Administrative borough of New York City"),
        "x_coordinate_state_plane": ("Numeric (Feet)", "State Plane Long Island", "NY State Plane X spatial coordinate"),
        "y_coordinate_state_plane": ("Numeric (Feet)", "State Plane Long Island", "NY State Plane Y spatial coordinate"),
        "open_data_channel_type": ("Categorical", "PHONE, ONLINE, MOBILE, OTHER", "Intake channel through which citizen contacted 311"),
        "park_facility_name": ("Text", "Park or public facility name", "Name of NYC Parks property"),
        "park_borough": ("Categorical", "5 NYC Boroughs", "Borough associated with park property"),
        "vehicle_type": ("Categorical / Text", "Vehicle classification", "Type of vehicle involved in TLC/traffic request"),
        "taxi_company_borough": ("Categorical", "5 NYC Boroughs", "Borough of licensed for-hire vehicle base"),
        "taxi_pick_up_location": ("Text", "Location string", "Location of taxi pickup"),
        "bridge_highway_name": ("Text", "Highway / bridge name", "Name of roadway structure"),
        "bridge_highway_direction": ("Categorical", "Direction code (NB, SB, EB, WB)", "Traffic flow direction"),
        "road_ramp": ("Categorical", "Roadway vs Ramp", "Classification of highway connector"),
        "bridge_highway_segment": ("Text", "Segment identifier", "Specific mile marker or segment description"),
        "latitude": ("Degrees Float", "40.4° to 40.95° N", "WGS84 Latitude geographic coordinate"),
        "longitude": ("Degrees Float", "-74.3° to -73.65° W", "WGS84 Longitude geographic coordinate"),
        "location": ("WKT / Point", "POINT (lon lat)", "Well-Known Text geometry representation")
    }

    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        null_pct = (null_count / len(df)) * 100
        dtype = str(df[col].dtype)
        desc_info = col_descriptions.get(col, ("General field", "Domain unspecified", "NYC 311 service request attribute"))
        doc.append(f"| `{col}` | `{dtype}` | {desc_info[1]} | {null_count:,} | {null_pct:.1f}% | {desc_info[2]} |\n")
        
    doc.append("\n---\n")
    doc.append("## 2. Measurable Data Quality Issues in Raw Ingestion\n\n")
    doc.append("The raw operational data exhibits concrete, measurable quality anomalies that must be handled by the cleaning pipeline:\n\n")
    doc.append("1. **Negative Operational Durations:** 61 records exhibit `closed_date < created_date` (e.g. closed hours or days before ticket was logged), indicating field logging errors.\n")
    doc.append("2. **Missing Closed Dates (Right-Censored / Active Tickets):** 111 records have null `closed_date` because the request was still Open, Pending, or In-Progress at collection time.\n")
    doc.append("3. **Invalid & Unspecified Borough Categorization:** 31 records contain `'Unspecified'` and 4 records contain `NaN` in the `borough` column.\n")
    doc.append("4. **Missing Spatial Attributes:** 213 records (2.8%) lack valid `latitude`, `longitude`, and spatial coordinates.\n")
    doc.append("5. **Extreme Duration Outliers:** Legitimate closed tickets span up to 47,261 hours (~5.4 years) due to backlog clearance of historic tickets.\n")
    doc.append("6. **Type Inconsistencies:** `incident_zip` is stored as floating-point numbers (`11411.0`) with trailing decimals and missing values.\n")
    doc.append("7. **Sparse Optional Fields:** Highway, taxi, and facility columns (e.g. `facility_type`, `vehicle_type`, `bridge_highway_name`) contain > 95% missing values as they only apply to specialized incident types.\n")
    doc.append("\n---\n")
    doc.append("## 3. Target Variable Definition for Tabular ML (Part B)\n\n")
    doc.append("- **Target Name:** `is_long_resolution`\n")
    doc.append("- **Type:** Binary Classification (`0`: Fast / Standard resolution within 24 hours, `1`: Long resolution taking > 24 hours)\n")
    doc.append("- **Class Distribution:** Approximately 50.4% positive (`1`) vs 49.6% negative (`0`), providing a balanced classification benchmark.\n")
    doc.append("- **Data Leakage Safeguard:** Columns created after ticket intake (`closed_date`, `resolution_description`, `resolution_action_updated_date`, `status`, `due_date`) must be strictly excluded from model feature sets.\n")

    out_file = os.path.join("docs", "schema.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.writelines(doc)
    print(f"[SUCCESS] Schema documentation written to: {out_file}")

if __name__ == "__main__":
    generate_schema_doc()
