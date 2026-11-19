# Name: Warisha / Data Engineering Student
# Roll Number: 2026-DS-0142
# Date: November 19, 2026

"""
Data Extraction Script
Fetches raw data from the official NYC Open Data 311 Service Requests API endpoint
Endpoint: https://data.cityofnewyork.us/resource/76ig-c548.csv
Saves raw, untouched records into data/raw/raw_311_data.csv.
"""

import os
import sys
import time
import requests

API_URL = "https://data.cityofnewyork.us/resource/76ig-c548.csv"
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "raw_311_data.csv")

def extract_raw_data(output_path=OUTPUT_PATH, limit=7500, force=False):
    """
    Extracts raw 311 service request records via Socrata SODA API.
    
    Parameters:
        output_path (str): Filepath where the raw CSV will be saved.
        limit (int): Number of rows to fetch (minimum required: 5,000).
        force (bool): If True, re-downloads even if the raw file exists.
        
    Returns:
        str: Absolute path to the saved raw CSV file.
    """
    if os.path.exists(output_path) and not force:
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[INFO] Raw data file already exists at: {output_path} ({file_size_mb:.2f} MB). Skipping download.")
        return output_path

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"[INFO] Connecting to NYC Open Data API: {API_URL}")
    print(f"[INFO] Requesting {limit} records from December 2019...")
    
    # Query parameters: we query a slice from December 2019 ordered by created_date
    params = {
        "$limit": limit,
        "$where": "created_date >= '2019-12-01T00:00:00' and created_date <= '2019-12-31T23:59:59'",
        "$order": "created_date ASC"
    }
    headers = {
        "User-Agent": "AntigravityReproduciblePipeline/1.0 (Educational Academic Project)",
        "Accept": "text/csv"
    }
    
    start_time = time.time()
    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=120)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch data from API: {e}", file=sys.stderr)
        raise

    elapsed = time.time() - start_time
    content = response.content
    file_size_kb = len(content) / 1024
    
    with open(output_path, "wb") as f:
        f.write(content)
        
    print(f"[SUCCESS] Downloaded {file_size_kb:.1f} KB in {elapsed:.2f}s.")
    print(f"[SUCCESS] Untouched raw data saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    force_download = "--force" in sys.argv
    extract_raw_data(force=force_download)
