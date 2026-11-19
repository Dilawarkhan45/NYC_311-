# Name: Warisha / Data Engineering Student
# Roll Number: 2026-DS-0142
# Date: November 19, 2026

"""
Data Cleaning Module for NYC 311 Service Requests.
Contains modular, tested functions for:
- Type fixes
- Category standardization
- Duplicate handling
- Duration calculation and invalid negative duration handling
- Geographic and duration outlier handling
- Missing value imputation / filtering
"""

import numpy as np
import pandas as pd

# NYC Geographic Bounding Box Limits
NYC_LAT_MIN = 40.48
NYC_LAT_MAX = 40.95
NYC_LON_MIN = -74.30
NYC_LON_MAX = -73.65
VALID_BOROUGHS = {"BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"}

def fix_datetime_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses date columns into pandas datetime objects.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with raw string date columns.
        
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
    Standardizes categorical string columns (stripping whitespace, consistent casing)
    and formats zip codes into clean 5-digit strings.
    
    Parameters:
        df (pd.DataFrame): Dataframe with raw categorical entries.
        
    Returns:
        pd.DataFrame: Standardized dataframe.
    """
    df = df.copy()
    
    # Standardize string fields
    for col in ["borough", "agency", "complaint_type", "open_data_channel_type", "city"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace({"NAN": np.nan, "NONE": np.nan, "": np.nan})
            
    # Normalize Boroughs: map non-standard values to NaN
    if "borough" in df.columns:
        df["borough"] = df["borough"].apply(lambda b: b if b in VALID_BOROUGHS else np.nan)
        
    # Standardize Zip code: remove trailing .0 if stored as float
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
    Identifies and removes duplicate records based on primary identifier and exact rows.
    
    Parameters:
        df (pd.DataFrame): Input dataframe.
        subset_col (str): Primary key column for uniqueness.
        
    Returns:
        pd.DataFrame: Deduplicated dataframe.
    """
    df = df.copy()
    # Remove exact duplicate rows
    df = df.drop_duplicates()
    # Remove duplicates on primary key
    if subset_col in df.columns:
        df = df.drop_duplicates(subset=[subset_col], keep="first")
    return df

def filter_invalid_durations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates ticket resolution time in hours and removes records where closed_date
    precedes created_date (negative duration logging errors).
    
    Parameters:
        df (pd.DataFrame): Dataframe with parsed created_date and closed_date.
        
    Returns:
        pd.DataFrame: Dataframe with resolution_time_hours computed and negative values filtered.
    """
    df = df.copy()
    if "created_date" in df.columns and "closed_date" in df.columns:
        duration_series = (df["closed_date"] - df["created_date"]).dt.total_seconds() / 3600.0
        df["resolution_time_hours"] = duration_series
        # Filter out records where closed_date is strictly before created_date (invalid data)
        # Note: Records where closed_date is NaN (still open) are kept with NaN duration
        is_negative = df["resolution_time_hours"] < 0
        df = df[~is_negative].copy()
    return df

def handle_outliers(df: pd.DataFrame, max_duration_hours: float = 8760.0) -> pd.DataFrame:
    """
    Handles spatial coordinates outside the valid NYC bounding box and caps or filters
    extreme duration outliers exceeding max_duration_hours (e.g. 1 year).
    
    Parameters:
        df (pd.DataFrame): Dataframe with latitude, longitude, and resolution_time_hours.
        max_duration_hours (float): Maximum plausible duration threshold in hours.
        
    Returns:
        pd.DataFrame: Dataframe with spatial outliers filtered and durations capped.
    """
    df = df.copy()
    
    # Filter spatial outliers outside NYC bounds if coordinates are present
    if "latitude" in df.columns and "longitude" in df.columns:
        has_coords = df["latitude"].notna() & df["longitude"].notna()
        valid_lat = (df["latitude"] >= NYC_LAT_MIN) & (df["latitude"] <= NYC_LAT_MAX)
        valid_lon = (df["longitude"] >= NYC_LON_MIN) & (df["longitude"] <= NYC_LON_MAX)
        
        # Keep rows that either have valid NYC coordinates or missing coordinates (to impute later)
        valid_coords_or_null = (~has_coords) | (valid_lat & valid_lon)
        df = df[valid_coords_or_null].copy()
        
    # Cap duration outliers exceeding 1 year (8760 hours) to prevent extreme skew
    if "resolution_time_hours" in df.columns:
        df["resolution_time_hours_raw"] = df["resolution_time_hours"]
        df["resolution_time_hours"] = df["resolution_time_hours"].clip(upper=max_duration_hours)
        
    return df

def clean_dataset(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    End-to-end cleaning pipeline orchestration executing all cleaning transformations.
    
    Parameters:
        raw_df (pd.DataFrame): Raw untouched dataframe.
        
    Returns:
        pd.DataFrame: Cleaned, structured dataframe ready for analysis and modeling.
    """
    df = raw_df.copy()
    df = fix_datetime_types(df)
    df = standardize_categories(df)
    df = handle_duplicates(df, subset_col="unique_key")
    df = filter_invalid_durations(df)
    df = handle_outliers(df)
    
    # Drop rows missing crucial operational columns needed for analysis
    # Require valid created_date, complaint_type, and valid borough
    df = df.dropna(subset=["created_date", "complaint_type", "borough"]).copy()
    
    return df
