# Name: Warisha / Data Engineering Student
# Roll Number: 2026-DS-0142
# Date: November 19, 2026

"""
Unit tests for data cleaning functions in src/clean.py.
Tests:
- fix_datetime_types
- standardize_categories
- handle_duplicates
- filter_invalid_durations
- handle_outliers
- clean_dataset
"""

import pytest
import pandas as pd
import numpy as np
from src.clean import (
    fix_datetime_types,
    standardize_categories,
    handle_duplicates,
    filter_invalid_durations,
    handle_outliers,
    clean_dataset
)

@pytest.fixture
def sample_raw_data():
    """Provides a synthetic dirty dataframe mirroring raw NYC 311 issues."""
    return pd.DataFrame({
        "unique_key": [101, 102, 103, 104, 104, 105],
        "created_date": [
            "2019-12-01T10:00:00.000",
            "2019-12-01T11:00:00.000",
            "2019-12-01T12:00:00.000",
            "2019-12-01T13:00:00.000",
            "2019-12-01T13:00:00.000",
            "2019-12-01T14:00:00.000"
        ],
        "closed_date": [
            "2019-12-01T15:00:00.000", # Normal: 5 hrs
            "2019-12-01T08:00:00.000", # Negative: -3 hrs (invalid)
            np.nan,                     # Open ticket: NaN
            "2019-12-02T13:00:00.000", # Duplicate ticket: 24 hrs
            "2019-12-02T13:00:00.000", # Duplicate row
            "2021-12-01T14:00:00.000"  # Extreme outlier: 17520 hrs (> 1 yr)
        ],
        "borough": [" brooklyn ", "BRONX", "Unspecified", "MANHATTAN", "MANHATTAN", "QUEENS"],
        "complaint_type": [" Noise - Street ", "HEAT/HOT WATER", "blocked driveway", "Illegal Parking", "Illegal Parking", "Street Condition"],
        "agency": ["nypd", "HPD", "NYPD", "nypd", "nypd", "DOT"],
        "incident_zip": [11201.0, "10451", "nan", 10001.0, 10001.0, "999999"],
        "latitude": [40.69, 40.82, 40.71, 55.12, 55.12, 40.74], # 55.12 is far outside NYC
        "longitude": [-73.98, -73.92, -74.00, -10.50, -10.50, -73.80], # -10.50 is outside NYC
        "open_data_channel_type": [" phone ", "ONLINE", "mobile", "PHONE", "PHONE", "OTHER"]
    })

def test_fix_datetime_types(sample_raw_data):
    """Verifies that string date columns are correctly parsed to datetime64."""
    df_fixed = fix_datetime_types(sample_raw_data)
    assert pd.api.types.is_datetime64_any_dtype(df_fixed["created_date"])
    assert pd.api.types.is_datetime64_any_dtype(df_fixed["closed_date"])
    assert df_fixed["closed_date"].isna().sum() == 1

def test_standardize_categories(sample_raw_data):
    """Verifies stripping whitespace, uppercase conversion, and invalid borough mapping."""
    df_clean = standardize_categories(sample_raw_data)
    assert df_clean["borough"].iloc[0] == "BROOKLYN"
    # Unspecified borough should be converted to NaN
    assert pd.isna(df_clean["borough"].iloc[2])
    # Agency and complaint_type should be uppercase and stripped
    assert df_clean["agency"].iloc[0] == "NYPD"
    assert df_clean["complaint_type"].iloc[0] == "NOISE - STREET"
    # Zip code float 11201.0 converted to clean string '11201'
    assert df_clean["incident_zip"].iloc[0] == "11201"
    assert pd.isna(df_clean["incident_zip"].iloc[2])

def test_handle_duplicates(sample_raw_data):
    """Verifies that duplicated rows and duplicate keys are dropped."""
    df_dedup = handle_duplicates(sample_raw_data, subset_col="unique_key")
    assert len(df_dedup) == 5
    assert df_dedup["unique_key"].nunique() == len(df_dedup)

def test_filter_invalid_durations(sample_raw_data):
    """Verifies that negative resolution durations are filtered out."""
    df_dates = fix_datetime_types(sample_raw_data)
    df_filtered = filter_invalid_durations(df_dates)
    # The negative duration row (index 1) should be removed
    assert 102 not in df_filtered["unique_key"].values
    assert (df_filtered["resolution_time_hours"].dropna() >= 0).all()

def test_handle_outliers(sample_raw_data):
    """Verifies filtering of spatial coordinates outside NYC and duration clipping."""
    df = fix_datetime_types(sample_raw_data)
    df = filter_invalid_durations(df)
    df_out = handle_outliers(df, max_duration_hours=8760.0)
    # Coordinates in row 104 (55.12, -10.50) are outside NYC and should be filtered
    assert 104 not in df_out["unique_key"].values
    # Extreme duration in 105 (>1 year) should be capped at 8760.0
    val_105 = df_out.loc[df_out["unique_key"] == 105, "resolution_time_hours"].values[0]
    assert val_105 == 8760.0

def test_clean_dataset_end_to_end(sample_raw_data):
    """Verifies end-to-end cleaning pipeline output shape and properties."""
    cleaned = clean_dataset(sample_raw_data)
    assert isinstance(cleaned, pd.DataFrame)
    assert not cleaned.empty
    # All remaining records must have valid borough, non-negative duration, valid coords
    assert cleaned["borough"].isin(["BROOKLYN", "QUEENS"]).all()
    assert (cleaned["resolution_time_hours"] >= 0).all()
    assert cleaned["unique_key"].is_unique
