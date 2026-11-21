# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
Data Cleaning Module for NYC 311 Service Requests (Part A).
Dataset: NYC Open Data 311 Service Requests (2010 - 2019)

Implements tested cleaning functions:
- fix_datetime_types: Parses ISO timestamps.
- standardize_categories: Normalizes casing, trims whitespace, standardizes zip codes and boroughs.
- handle_duplicates: Identifies and removes duplicate primary keys and duplicate rows.
- process_resolution_durations:
    * Computes regression target: resolution_hours = closed_date - created_date.
    * Separates invalid negative duration records into outputs/reports/rejected_rows.csv.
    * Preserves and flags exactly zero duration requests.
    * Tracks open requests (missing closed_date) without dropping them prematurely.
- handle_outliers: Identifies coordinates outside NYC bounds and caps extreme duration outliers.
- clean_dataset: End-to-end cleaning pipeline returning the cleaned master dataset and rejected rows.
"""

import os
import numpy as np
import pandas as pd

NYC_LAT_MIN = 40.48
NYC_LAT_MAX = 40.95
NYC_LON_MIN = -74.30
NYC_LON_MAX = -73.65
VALID_BOROUGHS = {"BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"}

def fix_datetime_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses date columns into standard pandas datetime objects.
    
    Parameters:
        df (pd.DataFrame): Dataframe with raw string date columns.
        
    Returns:
        pd.DataFrame: Dataframe with parsed datetime columns.
    """
    df = df.copy()
    for col in ["created_date", "closed_date", "due_date", "resolution_action_updated_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def standardize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes categorical string columns (stripping whitespace, consistent uppercase)
    and formats zip codes into clean 5-digit strings.
    
    Parameters:
        df (pd.DataFrame): Dataframe with raw categorical entries.
        
    Returns:
        pd.DataFrame: Standardized dataframe.
    """
    df = df.copy()
    
    for col in ["borough", "agency", "complaint_type", "open_data_channel_type", "city", "status"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace({"NAN": np.nan, "NONE": np.nan, "": np.nan})
            
    if "borough" in df.columns:
        df["borough"] = df["borough"].apply(lambda b: b if b in VALID_BOROUGHS else np.nan)
        
    if "incident_zip" in df.columns:
        def clean_zip(z):
            if pd.isna(z) or str(z).strip() in ["", "nan", "None"]:
                return np.nan
            z_str = str(z).split(".")[0].strip()
            if len(z_str) == 5 and z_str.isdigit():
                return z_str
            return np.nan
        df["incident_zip"] = df["incident_zip"].apply(clean_zip)
        
    return df

def handle_duplicates(df: pd.DataFrame, subset_col: str = "unique_key") -> pd.DataFrame:
    """
    Removes exact duplicated rows and ensures primary key uniqueness.
    
    Parameters:
        df (pd.DataFrame): Input dataframe.
        subset_col (str): Primary key column.
        
    Returns:
        pd.DataFrame: Deduplicated dataframe.
    """
    df = df.copy()
    df = df.drop_duplicates()
    if subset_col in df.columns:
        df = df.drop_duplicates(subset=[subset_col], keep="first")
    return df

def process_resolution_durations(df: pd.DataFrame, rejected_output_dir: str = "outputs/reports") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculates resolution_hours regression target.
    Separates negative durations into a dedicated rejected rows dataset with explicit reason.
    Keeps zero duration and open (NaN closed_date) records.
    
    Parameters:
        df (pd.DataFrame): Dataframe with parsed created_date and closed_date.
        rejected_output_dir (str): Directory where rejected_rows.csv will be saved.
        
    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (cleaned_df, rejected_df)
    """
    df = df.copy()
    if "created_date" not in df.columns or "closed_date" not in df.columns:
        return df, pd.DataFrame()
        
    duration_series = (df["closed_date"] - df["created_date"]).dt.total_seconds() / 3600.0
    df["resolution_hours"] = duration_series
    
    # Flag zero duration requests
    df["is_zero_duration"] = df["resolution_hours"] == 0.0
    
    # Negative durations represent chronological errors (closed before created)
    is_negative = df["resolution_hours"] < 0.0
    
    rejected_df = df[is_negative].copy()
    if not rejected_df.empty:
        rejected_df["rejection_reason"] = "Closed date earlier than created date (negative duration)"
        os.makedirs(rejected_output_dir, exist_ok=True)
        rej_file = os.path.join(rejected_output_dir, "rejected_rows.csv")
        export_cols = [c for c in ["unique_key", "created_date", "closed_date", "resolution_hours", "agency", "rejection_reason"] if c in rejected_df.columns]
        rejected_df[export_cols].to_csv(rej_file, index=False)
        
    cleaned_df = df[~is_negative].copy()
    return cleaned_df, rejected_df

def handle_outliers(df: pd.DataFrame, max_duration_hours: float = 8760.0) -> pd.DataFrame:
    """
    Validates geographical coordinates within NYC bounds and caps extreme resolution durations.
    
    Parameters:
        df (pd.DataFrame): Dataframe with latitude, longitude, and resolution_hours.
        max_duration_hours (float): Maximum realistic duration cap (default: 8760 hours = 1 year).
        
    Returns:
        pd.DataFrame: Outlier-adjusted dataframe.
    """
    df = df.copy()
    
    # Spatial bounds check
    if "latitude" in df.columns and "longitude" in df.columns:
        has_coords = df["latitude"].notna() & df["longitude"].notna()
        valid_lat = (df["latitude"] >= NYC_LAT_MIN) & (df["latitude"] <= NYC_LAT_MAX)
        valid_lon = (df["longitude"] >= NYC_LON_MIN) & (df["longitude"] <= NYC_LON_MAX)
        valid_coords_or_null = (~has_coords) | (valid_lat & valid_lon)
        df = df[valid_coords_or_null].copy()
        
    # Cap extreme duration outliers for summary stability while retaining raw in separate column
    if "resolution_hours" in df.columns:
        df["resolution_hours_raw"] = df["resolution_hours"]
        df["resolution_hours"] = df["resolution_hours"].clip(upper=max_duration_hours)
        # Compute log(1 + hours) for right-skewed regression modeling
        valid_hours = df["resolution_hours"].dropna()
        df["log_resolution_hours"] = np.nan
        df.loc[valid_hours.index, "log_resolution_hours"] = np.log1p(np.maximum(0, valid_hours.values))
        
    return df

def clean_dataset(raw_df: pd.DataFrame, rejected_output_dir: str = "outputs/reports") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    End-to-end cleaning pipeline execution.
    
    Parameters:
        raw_df (pd.DataFrame): Untouched raw dataframe.
        rejected_output_dir (str): Directory for rejected rows export.
        
    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (cleaned_df, rejected_df)
    """
    df = raw_df.copy()
    df = fix_datetime_types(df)
    df = standardize_categories(df)
    df = handle_duplicates(df, subset_col="unique_key")
    df, rejected_df = process_resolution_durations(df, rejected_output_dir=rejected_output_dir)
    df = handle_outliers(df)
    
    # Require non-null creation timestamp, complaint type, and valid borough for analysis
    df = df.dropna(subset=["created_date", "complaint_type", "borough"]).copy()
    return df, rejected_df
