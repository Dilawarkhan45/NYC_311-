# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
Unit tests for data cleaning functions in src/clean.py (Part A).
Tests:
- fix_datetime_types
- standardize_categories
- handle_duplicates
- process_resolution_durations (separating negative durations, keeping zero and open tickets)
- handle_outliers (NYC bounds and duration clipping)
- clean_dataset (end-to-end cleaning)
"""

import pytest
import pandas as pd
import numpy as np
from src.clean import (
    fix_datetime_types,
    standardize_categories,
    handle_duplicates,
    process_resolution_durations,
    handle_outliers,
    clean_dataset
)

@pytest.fixture
def sample_raw_data():
    """Provides a synthetic dirty dataframe representing NYC 311 operational data."""
    return pd.DataFrame({
        "unique_key": [101, 102, 103, 104, 104, 105, 106],
        "created_date": [
            "2015-06-01T10:00:00.000",
            "2015-06-01T11:00:00.000",
            "2015-06-01T12:00:00.000",
            "2015-06-01T13:00:00.000",
            "2015-06-01T13:00:00.000",
            "2015-06-01T14:00:00.000",
            "2015-06-01T15:00:00.000"
        ],
        "closed_date": [
            "2015-06-01T15:00:00.000", # Normal: 5.0 hrs
            "2015-06-01T08:00:00.000", # Chronological error: -3.0 hrs
            np.nan,                     # Open ticket: NaN
            "2015-06-02T13:00:00.000", # Duplicate key: 24.0 hrs
            "2015-06-02T13:00:00.000", # Duplicate row
            "2017-06-01T14:00:00.000", # Extreme outlier: 17520 hrs (> 1 yr)
            "2015-06-01T15:00:00.000"  # Zero duration: 0.0 hrs
        ],
        "borough": [" brooklyn ", "BRONX", "Unspecified", "MANHATTAN", "MANHATTAN", "QUEENS", "STATEN ISLAND"],
        "complaint_type": [" Noise - Street ", "HEAT/HOT WATER", "blocked driveway", "Illegal Parking", "Illegal Parking", "Street Condition", "Water System"],
        "agency": ["nypd", "HPD", "NYPD", "nypd", "nypd", "DOT", "DEP"],
        "incident_zip": [11201.0, "10451", "nan", 10001.0, 10001.0, "999999", "10301"],
        "latitude": [40.69, 40.82, 40.71, 55.12, 55.12, 40.74, 40.62],
        "longitude": [-73.98, -73.92, -74.00, -10.50, -10.50, -73.80, -74.08],
        "open_data_channel_type": [" phone ", "ONLINE", "mobile", "PHONE", "PHONE", "OTHER", "ONLINE"]
    })

def test_fix_datetime_types(sample_raw_data):
    """Verifies parsing of string dates to datetime64."""
    df_fixed = fix_datetime_types(sample_raw_data)
    assert pd.api.types.is_datetime64_any_dtype(df_fixed["created_date"])
    assert pd.api.types.is_datetime64_any_dtype(df_fixed["closed_date"])

def test_standardize_categories(sample_raw_data):
    """Verifies casing, whitespace trimming, and borough/zip standardization."""
    df_clean = standardize_categories(sample_raw_data)
    assert df_clean["borough"].iloc[0] == "BROOKLYN"
    assert pd.isna(df_clean["borough"].iloc[2]) # Unspecified mapped to NaN
    assert df_clean["agency"].iloc[0] == "NYPD"
    assert df_clean["incident_zip"].iloc[0] == "11201"

def test_handle_duplicates(sample_raw_data):
    """Verifies removal of duplicate rows and primary keys."""
    df_dedup = handle_duplicates(sample_raw_data, subset_col="unique_key")
    assert len(df_dedup) == 6
    assert df_dedup["unique_key"].is_unique

def test_process_resolution_durations(sample_raw_data, tmp_path):
    """Verifies separation of negative durations, retention of zero duration and open tickets."""
    df_dates = fix_datetime_types(sample_raw_data)
    cleaned, rejected = process_resolution_durations(df_dates, rejected_output_dir=str(tmp_path))
    
    # 1 negative duration record (key 102) should be separated into rejected
    assert len(rejected) == 1
    assert rejected["unique_key"].iloc[0] == 102
    assert "rejection_reason" in rejected.columns
    
    # Cleaned dataset retains non-negative durations and open tickets
    assert 102 not in cleaned["unique_key"].values
    assert (cleaned["resolution_hours"].dropna() >= 0).all()
    
    # Zero duration ticket (key 106) is retained and flagged
    assert cleaned.loc[cleaned["unique_key"] == 106, "is_zero_duration"].iloc[0] == True
    
    # Open ticket (key 103) is retained with NaN resolution_hours
    assert pd.isna(cleaned.loc[cleaned["unique_key"] == 103, "resolution_hours"].iloc[0])

def test_handle_outliers(sample_raw_data, tmp_path):
    """Verifies coordinate filtering outside NYC and duration clipping."""
    df = fix_datetime_types(sample_raw_data)
    cleaned, _ = process_resolution_durations(df, rejected_output_dir=str(tmp_path))
    outlier_df = handle_outliers(cleaned, max_duration_hours=8760.0)
    
    # Coordinates in key 104 are outside NYC bounds (lat=55.12, lon=-10.50)
    assert 104 not in outlier_df["unique_key"].values
    
    # Extreme duration in 105 (>1 year) capped at 8760.0
    val_105 = outlier_df.loc[outlier_df["unique_key"] == 105, "resolution_hours"].iloc[0]
    assert val_105 == 8760.0
    assert "log_resolution_hours" in outlier_df.columns

def test_clean_dataset_end_to_end(sample_raw_data, tmp_path):
    """Verifies end-to-end cleaning output."""
    cleaned, rejected = clean_dataset(sample_raw_data, rejected_output_dir=str(tmp_path))
    assert not cleaned.empty
    assert (cleaned["resolution_hours"].dropna() >= 0).all()
    assert cleaned["borough"].isin(["BROOKLYN", "QUEENS", "STATEN ISLAND"]).all()
    assert cleaned["unique_key"].is_unique
