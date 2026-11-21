# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
Feature Engineering and Statistical Summaries Module (Part A).
Dataset: NYC Open Data 311 Service Requests (2010 - 2019)

Vectorized NumPy operations:
1. Target transformation: resolution_hours and log_resolution_hours = np.log1p(hours).
2. Spatial Haversine distance: distance_to_center_km from NYC City Hall.
3. Temporal indicator: is_weekend = np.where(dayofweek >= 5, 1, 0).

Pandas analytical summaries:
1. Groupby & Aggregations: Borough-level count, mean, median, standard deviation of resolution_hours.
2. Pivot Table: Agency vs Borough complaint volume cross-tabulation.
3. Frequency Distributions: Top 15 complaint types and citizen intake channel shares.
"""

import os
import numpy as np
import pandas as pd

NYC_CENTER_LAT = 40.7128
NYC_CENTER_LON = -74.0060
EARTH_RADIUS_KM = 6371.0088

def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes vectorized spatial, temporal, and regression target features.
    
    Parameters:
        df (pd.DataFrame): Cleaned 311 service request dataframe.
        
    Returns:
        pd.DataFrame: Enriched dataframe with added feature columns.
    """
    df = df.copy()
    
    # 1. Temporal feature extraction
    if "created_date" in df.columns and pd.api.types.is_datetime64_any_dtype(df["created_date"]):
        df["created_year"] = df["created_date"].dt.year
        df["created_month"] = df["created_date"].dt.month
        df["created_hour"] = df["created_date"].dt.hour
        df["created_day_of_week"] = df["created_date"].dt.dayofweek # 0=Monday, 6=Sunday
        df["is_weekend"] = np.where(df["created_day_of_week"] >= 5, 1, 0)
        
    # 2. Vectorized Haversine distance from NYC City Hall
    if "latitude" in df.columns and "longitude" in df.columns:
        lat1 = np.radians(NYC_CENTER_LAT)
        lon1 = np.radians(NYC_CENTER_LON)
        lat2 = np.radians(df["latitude"].values)
        lon2 = np.radians(df["longitude"].values)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
        c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
        df["distance_to_center_km"] = EARTH_RADIUS_KM * c
        
    # 3. Vectorized Logarithmic Transformation for skewed resolution hours
    if "resolution_hours" in df.columns:
        valid_idx = df["resolution_hours"].dropna().index
        df["log_resolution_hours"] = np.nan
        df.loc[valid_idx, "log_resolution_hours"] = np.log1p(np.maximum(0, df.loc[valid_idx, "resolution_hours"].values))
        
    return df

def generate_pandas_summaries(df: pd.DataFrame, output_dir: str = "outputs/reports") -> dict:
    """
    Generates summary statistics, groupby aggregations, pivot tables, and value counts.
    
    Parameters:
        df (pd.DataFrame): Enriched dataframe.
        output_dir (str): Destination directory for CSV summaries.
        
    Returns:
        dict: Summary DataFrames dictionary.
    """
    os.makedirs(output_dir, exist_ok=True)
    summaries = {}
    
    # 1. Groupby & Agg: Borough resolution metrics
    if "borough" in df.columns and "resolution_hours" in df.columns:
        valid_res = df.dropna(subset=["resolution_hours"])
        borough_summary = valid_res.groupby("borough")["resolution_hours"].agg(
            ticket_count="count",
            mean_resolution_hours="mean",
            median_resolution_hours="median",
            std_resolution_hours="std",
            min_resolution_hours="min",
            max_resolution_hours="max"
        ).reset_index()
        
        # Add zero-duration ticket counts
        if "is_zero_duration" in df.columns:
            zero_counts = df.groupby("borough")["is_zero_duration"].sum().reset_index()
            zero_counts.columns = ["borough", "zero_duration_tickets"]
            borough_summary = borough_summary.merge(zero_counts, on="borough", how="left")
            
        b_file = os.path.join(output_dir, "borough_summary.csv")
        borough_summary.to_csv(b_file, index=False)
        summaries["borough_summary"] = borough_summary
        
    # 2. Pivot Table: Agency vs Borough ticket volume
    if "agency" in df.columns and "borough" in df.columns:
        top_agencies = df["agency"].value_counts().head(6).index
        filtered = df[df["agency"].isin(top_agencies)]
        agency_borough_pivot = pd.pivot_table(
            filtered,
            values="unique_key",
            index="agency",
            columns="borough",
            aggfunc="count",
            fill_value=0
        )
        p_file = os.path.join(output_dir, "agency_borough_pivot.csv")
        agency_borough_pivot.to_csv(p_file)
        summaries["agency_borough_pivot"] = agency_borough_pivot
        
    # 3. Value counts: Top Complaint Types and Channel Distribution
    if "complaint_type" in df.columns:
        top_comp = df["complaint_type"].value_counts().head(15).reset_index()
        top_comp.columns = ["complaint_type", "count"]
        top_comp["percentage"] = (top_comp["count"] / len(df) * 100).round(2)
        c_file = os.path.join(output_dir, "top_complaint_types.csv")
        top_comp.to_csv(c_file, index=False)
        summaries["top_complaints"] = top_comp
        
    if "open_data_channel_type" in df.columns:
        channel_dist = df["open_data_channel_type"].value_counts(dropna=False).reset_index()
        channel_dist.columns = ["intake_channel", "count"]
        channel_dist["percentage"] = (channel_dist["count"] / len(df) * 100).round(2)
        ch_file = os.path.join(output_dir, "channel_distribution.csv")
        channel_dist.to_csv(ch_file, index=False)
        summaries["channel_distribution"] = channel_dist
        
    print(f"[SUCCESS] Summary tables written to: {output_dir}")
    return summaries
