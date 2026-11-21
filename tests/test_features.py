# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
Unit tests for feature engineering and statistical summaries in src/features.py (Part A).
Tests:
- add_engineered_features: resolution_hours, log_resolution_hours, Haversine distance, temporal indicators.
- generate_pandas_summaries: Groupby aggregations, pivot table, and value counts.
"""

import os
import pytest
import pandas as pd
import numpy as np
from src.features import add_engineered_features, generate_pandas_summaries

@pytest.fixture
def sample_cleaned_df():
    """Provides a sample cleaned dataframe with coordinates, timestamps, and resolution hours."""
    return pd.DataFrame({
        "unique_key": [201, 202, 203, 204],
        "created_date": pd.to_datetime([
            "2015-06-07 08:00:00", # Sunday (weekend)
            "2015-06-08 09:00:00", # Monday (weekday)
            "2015-06-09 14:00:00", # Tuesday (weekday)
            "2015-06-10 16:00:00"  # Wednesday (weekday)
        ]),
        "closed_date": pd.to_datetime([
            "2015-06-07 18:00:00", # 10 hours
            "2015-06-09 15:00:00", # 30 hours
            "2015-06-11 14:00:00", # 48 hours
            "2015-06-10 16:00:00"  # 0 hours (zero duration)
        ]),
        "resolution_hours": [10.0, 30.0, 48.0, 0.0],
        "is_zero_duration": [False, False, False, True],
        "borough": ["BROOKLYN", "MANHATTAN", "QUEENS", "BROOKLYN"],
        "agency": ["NYPD", "HPD", "DOT", "NYPD"],
        "complaint_type": ["NOISE - RESIDENTIAL", "HEAT/HOT WATER", "STREET CONDITION", "ILLEGAL PARKING"],
        "open_data_channel_type": ["PHONE", "ONLINE", "MOBILE", "PHONE"],
        "latitude": [40.6782, 40.7831, 40.7282, 40.6900],
        "longitude": [-73.9442, -73.9712, -73.7949, -73.9900]
    })

def test_add_engineered_features(sample_cleaned_df):
    """Verifies temporal extraction, Haversine distance, and log-transformed target."""
    df_feat = add_engineered_features(sample_cleaned_df)
    
    # Temporal attributes
    assert "created_hour" in df_feat.columns
    assert "is_weekend" in df_feat.columns
    assert df_feat.loc[0, "is_weekend"] == 1 # Sunday
    assert df_feat.loc[1, "is_weekend"] == 0 # Monday
    
    # Spatial distance
    assert "distance_to_center_km" in df_feat.columns
    assert (df_feat["distance_to_center_km"] > 0).all()
    assert (df_feat["distance_to_center_km"] < 50).all()
    
    # Log-transformed resolution hours
    assert "log_resolution_hours" in df_feat.columns
    assert (df_feat["log_resolution_hours"] >= 0).all()
    # Check np.log1p(0) == 0.0 for zero duration record
    assert df_feat.loc[3, "log_resolution_hours"] == 0.0

def test_generate_pandas_summaries(sample_cleaned_df, tmp_path):
    """Verifies that groupby, pivot_table, and value_counts generate output CSV reports."""
    df_feat = add_engineered_features(sample_cleaned_df)
    out_dir = tmp_path / "reports"
    summaries = generate_pandas_summaries(df_feat, output_dir=str(out_dir))
    
    assert "borough_summary" in summaries
    assert "agency_borough_pivot" in summaries
    assert "top_complaints" in summaries
    assert "channel_distribution" in summaries
    
    assert (out_dir / "borough_summary.csv").exists()
    assert (out_dir / "agency_borough_pivot.csv").exists()
