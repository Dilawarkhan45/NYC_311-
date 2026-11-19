# Name: Warisha / Data Engineering Student
# Roll Number: 2026-DS-0142
# Date: November 19, 2026

"""
Unit tests for feature engineering and statistical summaries in src/features.py.
Tests:
- add_engineered_features (vectorized target, vectorized distance, temporal features)
- generate_pandas_summaries (groupby, pivot_table, value_counts)
"""

import os
import pytest
import pandas as pd
import numpy as np
from src.features import add_engineered_features, generate_pandas_summaries

@pytest.fixture
def sample_cleaned_df():
    """Provides a sample cleaned dataframe with datetime, borough, coordinates, and duration."""
    return pd.DataFrame({
        "unique_key": [201, 202, 203, 204],
        "created_date": pd.to_datetime([
            "2019-12-01 08:00:00", # Sunday (weekend)
            "2019-12-02 09:00:00", # Monday (weekday)
            "2019-12-03 14:00:00", # Tuesday (weekday)
            "2019-12-04 16:00:00"  # Wednesday (weekday)
        ]),
        "closed_date": pd.to_datetime([
            "2019-12-01 18:00:00", # 10 hours (short <= 24)
            "2019-12-03 15:00:00", # 30 hours (long > 24)
            "2019-12-05 14:00:00", # 48 hours (long > 24)
            "2019-12-04 20:00:00"  # 4 hours (short <= 24)
        ]),
        "resolution_time_hours": [10.0, 30.0, 48.0, 4.0],
        "borough": ["BROOKLYN", "MANHATTAN", "QUEENS", "BROOKLYN"],
        "agency": ["NYPD", "HPD", "DOT", "NYPD"],
        "complaint_type": ["NOISE - RESIDENTIAL", "HEAT/HOT WATER", "STREET CONDITION", "ILLEGAL PARKING"],
        "open_data_channel_type": ["PHONE", "ONLINE", "MOBILE", "PHONE"],
        "latitude": [40.6782, 40.7831, 40.7282, 40.6900],
        "longitude": [-73.9442, -73.9712, -73.7949, -73.9900]
    })

def test_add_engineered_features(sample_cleaned_df):
    """Verifies temporal extraction, vectorized distance, and vectorized target."""
    df_feat = add_engineered_features(sample_cleaned_df)
    
    # Check temporal features
    assert "created_hour" in df_feat.columns
    assert "is_weekend" in df_feat.columns
    assert df_feat.loc[0, "is_weekend"] == 1 # Sunday
    assert df_feat.loc[1, "is_weekend"] == 0 # Monday
    
    # Check vectorized target: is_long_resolution
    assert "is_long_resolution" in df_feat.columns
    assert list(df_feat["is_long_resolution"].values) == [0, 1, 1, 0]
    
    # Check vectorized Haversine distance
    assert "distance_to_center_km" in df_feat.columns
    assert (df_feat["distance_to_center_km"] > 0).all()
    assert (df_feat["distance_to_center_km"] < 50).all() # Within NYC metro radius

def test_generate_pandas_summaries(sample_cleaned_df, tmp_path):
    """Verifies that groupby, pivot_table, and value_counts generate output CSV files."""
    df_feat = add_engineered_features(sample_cleaned_df)
    out_dir = tmp_path / "reports"
    summaries = generate_pandas_summaries(df_feat, output_dir=str(out_dir))
    
    assert "borough_summary" in summaries
    assert "agency_borough_pivot" in summaries
    assert "top_complaints" in summaries
    assert "channel_distribution" in summaries
    
    assert (out_dir / "borough_summary.csv").exists()
    assert (out_dir / "agency_borough_pivot.csv").exists()
