# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
SQLite Database Integration Module (Part A).
Loads cleaned 311 tickets into an embedded SQLite database (data/nyc_311.db),
creates the normalized demographic lookup table, and executes relational JOIN queries.
"""

import os
import sqlite3
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "nyc_311.db")

BOROUGH_DEMOGRAPHICS = pd.DataFrame({
    "borough": ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"],
    "population": [1472654, 2736074, 1694251, 2405464, 495747],
    "land_area_sq_mi": [42.10, 70.82, 22.83, 108.53, 58.37]
})

def run_sqlite_pipeline(cleaned_df: pd.DataFrame, db_path: str = DB_PATH, output_dir: str = "outputs/reports") -> pd.DataFrame:
    """
    Loads data into SQLite, executes the relational JOIN query, and exports results.
    
    Parameters:
        cleaned_df (pd.DataFrame): Cleaned 311 dataset.
        db_path (str): SQLite database destination path.
        output_dir (str): Output directory for query results CSV.
        
    Returns:
        pd.DataFrame: Formatted SQL query output.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    cols = [
        "unique_key", "created_date", "closed_date", "agency", 
        "complaint_type", "borough", "resolution_hours", 
        "is_zero_duration", "open_data_channel_type"
    ]
    valid_cols = [c for c in cols if c in cleaned_df.columns]
    sql_df = cleaned_df[valid_cols].copy()
    
    for dt_col in ["created_date", "closed_date"]:
        if dt_col in sql_df.columns:
            sql_df[dt_col] = sql_df[dt_col].astype(str)
            
    conn = sqlite3.connect(db_path)
    
    try:
        sql_df.to_sql("tickets", conn, if_exists="replace", index=False)
        BOROUGH_DEMOGRAPHICS.to_sql("borough_lookup", conn, if_exists="replace", index=False)
        
        sql_query = """
        SELECT 
            b.borough AS borough_name,
            b.population AS census_population,
            b.land_area_sq_mi,
            COUNT(t.unique_key) AS total_service_requests,
            ROUND((COUNT(t.unique_key) * 10000.0) / b.population, 2) AS requests_per_10k_residents,
            ROUND(AVG(t.resolution_hours), 2) AS avg_resolution_hours,
            ROUND(
                SUM(CASE WHEN t.is_zero_duration = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(t.unique_key),
                2
            ) AS pct_zero_duration_tickets
        FROM borough_lookup b
        INNER JOIN tickets t ON b.borough = t.borough
        GROUP BY 
            b.borough, 
            b.population, 
            b.land_area_sq_mi
        ORDER BY 
            requests_per_10k_residents DESC;
        """
        
        result_df = pd.read_sql_query(sql_query, conn)
        out_csv = os.path.join(output_dir, "sqlite_query_results.csv")
        result_df.to_csv(out_csv, index=False)
        
        print(f"[SUCCESS] SQLite query successfully executed and exported to: {out_csv}")
        print("\n--- SQLite Query Results: Per-Capita 311 Demands & Adherence ---")
        print(result_df.to_string(index=False))
        print("-----------------------------------------------------------------\n")
        return result_df
        
    finally:
        conn.close()

if __name__ == "__main__":
    cleaned_path = os.path.join("data", "cleaned", "cleaned_311_data.csv")
    if os.path.exists(cleaned_path):
        df = pd.read_csv(cleaned_path)
        run_sqlite_pipeline(df)
    else:
        print(f"[WARN] Cleaned dataset not found at {cleaned_path}. Run pipeline first.")
