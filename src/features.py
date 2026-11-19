# Name: Warisha / Data Engineering Student
# Roll Number: 2026-DS-0142
# Date: November 19, 2026

"""
Feature Engineering and Statistical Summaries Module.
Implements:
- NumPy vectorized operations:
  1. Vectorized binary target derivation using np.where (is_long_resolution)
  2. Vectorized Haversine spherical distance computation from NYC geographic center
  3. Vectorized logarithmic transformation with np.log1p
- Pandas analytical grouping & summary statistics:
  1. Groupby and agg metrics (mean, median, std, count by Borough and Agency)
  2. Pivot table of Agency vs Borough ticket resolution rates
  3. Value counts of Complaint Types and Intake Channels
"""

import os
import numpy as np
import pandas as pd

# NYC Reference Landmark: City Hall coordinates (Manhattan)
NYC_CENTER_LAT = 40.7128
NYC_CENTER_LON = -74.0060
EARTH_RADIUS_KM = 6371.0088

def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies vectorized transformations to enrich the dataset with spatial,
    temporal, and target attributes.
    
    Parameters:
        df (pd.DataFrame): Cleaned 311 service request dataframe.
        
    Returns:
        pd.DataFrame: Dataframe with added engineered features.
    """
    df = df.copy()
    
    # 1. Temporal feature extraction from created_date
    if "created_date" in df.columns and pd.api.types.is_datetime64_any_dtype(df["created_date"]):
        df["created_hour"] = df["created_date"].dt.hour
        df["created_day_of_week"] = df["created_date"].dt.dayofweek # 0=Monday, 6=Sunday
        df["is_weekend"] = np.where(df["created_day_of_week"] >= 5, 1, 0)
        
    # 2. Vectorized Operation 1 (NumPy): Target variable construction
    # Target: is_long_resolution (1 if duration > 24 hours, 0 if <= 24 hours)
    if "resolution_time_hours" in df.columns:
        df["is_long_resolution"] = np.where(df["resolution_time_hours"] > 24.0, 1, 0)
        # Handle open tickets (where resolution_time_hours is NaN)
        df.loc[df["resolution_time_hours"].isna(), "is_long_resolution"] = np.nan
        
    # 3. Vectorized Operation 2 (NumPy): Haversine distance from NYC Center (City Hall)
    if "latitude" in df.columns and "longitude" in df.columns:
        lat1 = np.radians(NYC_CENTER_LAT)
        lon1 = np.radians(NYC_CENTER_LON)
        lat2 = np.radians(df["latitude"].values)
        lon2 = np.radians(df["longitude"].values)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Haversine formula
        a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
        # Use np.clip to prevent floating point domain errors in arcsin
        c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
        df["distance_to_center_km"] = EARTH_RADIUS_KM * c
        
    # 4. Vectorized Operation 3 (NumPy): Logarithmic duration for regression skew handling
    if "resolution_time_hours" in df.columns:
        valid_duration = df["resolution_time_hours"].dropna()
        df["log_resolution_time"] = np.nan
        df.loc[valid_duration.index, "log_resolution_time"] = np.log1p(valid_duration.values)
        
    return df

def generate_pandas_summaries(df: pd.DataFrame, output_dir: str = "outputs/reports") -> dict:
    """
    Computes summary statistics, groupby aggregations, pivot tables,
    and frequency distributions using Pandas.
    
    Parameters:
        df (pd.DataFrame): Enriched dataframe.
        output_dir (str): Directory where CSV summary reports are saved.
        
    Returns:
        dict: Dictionary containing summary DataFrames.
    """
    os.makedirs(output_dir, exist_ok=True)
    summaries = {}
    
    # 1. Groupby and Aggregation: Borough resolution performance
    if "borough" in df.columns and "resolution_time_hours" in df.columns:
        borough_summary = df.groupby("borough")["resolution_time_hours"].agg(
            ticket_count="count",
            mean_resolution_hours="mean",
            median_resolution_hours="median",
            std_resolution_hours="std",
            min_resolution_hours="min",
            max_resolution_hours="max"
        ).reset_index()
        
        # Add long ticket rate
        if "is_long_resolution" in df.columns:
            long_rate = df.groupby("borough")["is_long_resolution"].mean().reset_index()
            borough_summary["long_ticket_rate_pct"] = (long_rate["is_long_resolution"] * 100).round(2)
            
        borough_file = os.path.join(output_dir, "borough_summary.csv")
        borough_summary.to_csv(borough_file, index=False)
        summaries["borough_summary"] = borough_summary
        
    # 2. Pivot Table: Agency vs Borough ticket volume
    if "agency" in df.columns and "borough" in df.columns:
        top_agencies = df["agency"].value_counts().head(6).index
        filtered_df = df[df["agency"].isin(top_agencies)]
        agency_borough_pivot = pd.pivot_table(
            filtered_df,
            values="unique_key",
            index="agency",
            columns="borough",
            aggfunc="count",
            fill_value=0
        )
        pivot_file = os.path.join(output_dir, "agency_borough_pivot.csv")
        agency_borough_pivot.to_csv(pivot_file)
        summaries["agency_borough_pivot"] = agency_borough_pivot
        
    # 3. Value Counts: Top Complaint Types and Channel Distribution
    if "complaint_type" in df.columns:
        top_complaints = df["complaint_type"].value_counts().head(15).reset_index()
        top_complaints.columns = ["complaint_type", "count"]
        top_complaints["percentage"] = (top_complaints["count"] / len(df) * 100).round(2)
        complaints_file = os.path.join(output_dir, "top_complaint_types.csv")
        top_complaints.to_csv(complaints_file, index=False)
        summaries["top_complaints"] = top_complaints
        
    if "open_data_channel_type" in df.columns:
        channel_dist = df["open_data_channel_type"].value_counts(dropna=False).reset_index()
        channel_dist.columns = ["intake_channel", "count"]
        channel_dist["percentage"] = (channel_dist["count"] / len(df) * 100).round(2)
        channel_file = os.path.join(output_dir, "channel_distribution.csv")
        channel_dist.to_csv(channel_file, index=False)
        summaries["channel_distribution"] = channel_dist
        
    print(f"[SUCCESS] Summary reports successfully written to: {output_dir}")
    return summaries
