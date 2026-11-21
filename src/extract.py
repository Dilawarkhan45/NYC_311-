# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
Data Extraction Module for NYC 311 Service Requests.
Source: NYC Open Data SODA API (Endpoint: https://data.cityofnewyork.us/resource/76ig-c548.csv)

Implementation:
Downloads a stratified, time-based sample of 20,000 records from 2010 to 2019:
- 2,000 requests per year spread over all 12 months (~167 per month).
- Fixed random seed ensures exact reproducibility.
- Saves untouched raw data to data/raw/raw_311_data.csv.
"""

import os
import sys
import time
import random
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pandas as pd

API_URL = "https://data.cityofnewyork.us/resource/76ig-c548.csv"
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "raw_311_data.csv")
RANDOM_SEED = 42

def fetch_month_slice(year: int, month: int, target_rows: int = 167) -> pd.DataFrame:
    """
    Fetches a reproducible slice of service requests for a given year and month.
    
    Parameters:
        year (int): Calendar year (2010 - 2019).
        month (int): Calendar month (1 - 12).
        target_rows (int): Number of consecutive rows to fetch.
        
    Returns:
        pd.DataFrame: Sliced dataframe for the month.
    """
    m_str = f"{month:02d}"
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1
    next_str = f"{next_m:02d}"
    
    start_date = f"{year}-{m_str}-01T00:00:00"
    end_date = f"{next_y}-{next_str}-01T00:00:00"
    
    # Deterministic pseudo-random offset using fixed seed
    rng = random.Random(RANDOM_SEED * 1000 + year * 12 + month)
    offset = rng.randint(20, 200)
    
    params = {
        "$limit": target_rows,
        "$offset": offset,
        "$where": f"created_date >= '{start_date}' and created_date < '{end_date}'",
        "$order": "created_date ASC"
    }
    headers = {
        "User-Agent": "NYC311ReproducibleResearch/1.0 (Academic Dilawar Khan TRN-2026-000961)",
        "Accept": "text/csv"
    }
    
    response = requests.get(API_URL, params=params, headers=headers, timeout=45)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text), low_memory=False)
    return df

def extract_raw_data(output_path: str = OUTPUT_PATH, total_target: int = 20000, force: bool = False) -> str:
    """
    Coordinates extraction of 20,000 stratified records across 2010-2019.
    
    Parameters:
        output_path (str): Destination path for the raw CSV.
        total_target (int): Target row count (20,000).
        force (bool): If True, re-downloads even if the file exists.
        
    Returns:
        str: Absolute path to the saved raw CSV.
    """
    if os.path.exists(output_path) and not force:
        try:
            existing_df = pd.read_csv(output_path, low_memory=False)
            if len(existing_df) >= 20000:
                years = pd.to_datetime(existing_df["created_date"], errors="coerce").dt.year.dropna().unique()
                if len(years) >= 8: # Multi-year stratified sample confirmed
                    print(f"[INFO] Stratified raw data already exists at: {output_path} ({len(existing_df):,} rows spanning {sorted(years)}). Skipping download.")
                    return output_path
        except Exception:
            pass

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"[INFO] Extracting stratified time-based sample of {total_target:,} records from NYC Open Data (2010 to 2019)...")
    start_time = time.time()
    
    month_slices = []
    # 10 years (2010-2019) * 12 months = 120 months. 167 rows * 120 = 20,040 rows.
    tasks = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        for year in range(2010, 2020):
            for month in range(1, 13):
                tasks.append(executor.submit(fetch_month_slice, year, month, 167))
                
        for future in as_completed(tasks):
            try:
                df_slice = future.result()
                if not df_slice.empty:
                    month_slices.append(df_slice)
            except Exception as e:
                print(f"[WARN] Failed to fetch slice: {e}", file=sys.stderr)

    if not month_slices:
        raise RuntimeError("No data slices were successfully retrieved from the API.")

    combined_df = pd.concat(month_slices, ignore_index=True)
    combined_df = combined_df.sort_values(by="created_date").head(total_target)
    
    combined_df.to_csv(output_path, index=False)
    elapsed = time.time() - start_time
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    
    print(f"[SUCCESS] Ingested {len(combined_df):,} rows and {len(combined_df.columns)} columns in {elapsed:.2f}s ({file_size_mb:.2f} MB).")
    print(f"[SUCCESS] Untouched raw data saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    force_run = "--force" in sys.argv
    extract_raw_data(force=force_run)
