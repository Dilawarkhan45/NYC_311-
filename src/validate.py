# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
Data Validation Module for NYC 311 Service Requests (Part A).
Implements testable validation checks:
- validate_uniqueness: Primary key uniqueness.
- validate_types: Expected dtypes for identifiers, dates, and coordinates.
- validate_null_constraints: Zero nulls allowed in critical business fields.
- validate_ranges: Valid GPS bounds and non-negative resolution hours.
- run_quality_gate: Enforces Quality Gate threshold (>=95.0%) and outputs metrics.json.
"""

import os
import json
import pandas as pd
import numpy as np

class ValidationError(Exception):
    """Raised when data integrity validation fails."""
    pass

class QualityGateError(Exception):
    """Raised when data quality pass rate falls below the required threshold."""
    pass

def validate_uniqueness(df: pd.DataFrame, primary_key: str = "unique_key") -> bool:
    """
    Validates that the primary key has no duplicate values.
    
    Parameters:
        df (pd.DataFrame): Dataset to validate.
        primary_key (str): Primary key column name.
        
    Returns:
        bool: True if strictly unique.
        
    Raises:
        ValidationError: If duplicate keys are detected.
    """
    if primary_key not in df.columns:
        raise ValidationError(f"Primary key '{primary_key}' missing from dataframe.")
    duplicates = df[primary_key].duplicated().sum()
    if duplicates > 0:
        raise ValidationError(f"Uniqueness check failed: found {duplicates} duplicate values in '{primary_key}'.")
    return True

def validate_types(df: pd.DataFrame) -> bool:
    """
    Validates that critical columns conform to expected data types.
    
    Parameters:
        df (pd.DataFrame): Dataset to validate.
        
    Returns:
        bool: True if type validation passes.
        
    Raises:
        ValidationError: If types mismatch.
    """
    if "unique_key" in df.columns and not pd.api.types.is_numeric_dtype(df["unique_key"]):
        raise ValidationError("Type check failed: 'unique_key' must be numeric.")
        
    for date_col in ["created_date", "closed_date"]:
        if date_col in df.columns and not df[date_col].dropna().empty:
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                raise ValidationError(f"Type check failed: '{date_col}' must be datetime.")
                
    for num_col in ["latitude", "longitude"]:
        if num_col in df.columns and not df[num_col].dropna().empty:
            if not pd.api.types.is_float_dtype(df[num_col]):
                raise ValidationError(f"Type check failed: '{num_col}' must be float.")
    return True

def validate_null_constraints(df: pd.DataFrame, critical_cols: list = None) -> bool:
    """
    Validates that essential business columns have zero null values.
    
    Parameters:
        df (pd.DataFrame): Dataset to validate.
        critical_cols (list): Columns that must not contain null values.
        
    Returns:
        bool: True if no nulls are found in critical columns.
        
    Raises:
        ValidationError: If null values exist in critical columns.
    """
    if critical_cols is None:
        critical_cols = ["unique_key", "created_date", "complaint_type", "borough"]
        
    for col in critical_cols:
        if col not in df.columns:
            raise ValidationError(f"Critical column '{col}' missing for null check.")
        null_count = df[col].isnull().sum()
        if null_count > 0:
            raise ValidationError(f"Null constraint violated: column '{col}' has {null_count} null entries.")
    return True

def validate_ranges(df: pd.DataFrame) -> bool:
    """
    Validates range boundaries:
    - Coordinates must be within greater NYC bounds.
    - Resolution duration must be non-negative.
    
    Parameters:
        df (pd.DataFrame): Dataset to validate.
        
    Returns:
        bool: True if all range checks pass.
        
    Raises:
        ValidationError: If values fall outside defined ranges.
    """
    if "resolution_hours" in df.columns:
        neg_count = (df["resolution_hours"] < 0).sum()
        if neg_count > 0:
            raise ValidationError(f"Range check failed: found {neg_count} records with negative resolution hours.")
            
    if "latitude" in df.columns and "longitude" in df.columns:
        coords_mask = df["latitude"].notna() & df["longitude"].notna()
        if coords_mask.any():
            bad_lat = ((df.loc[coords_mask, "latitude"] < 40.48) | (df.loc[coords_mask, "latitude"] > 40.95)).sum()
            bad_lon = ((df.loc[coords_mask, "longitude"] < -74.30) | (df.loc[coords_mask, "longitude"] > -73.65)).sum()
            if bad_lat > 0 or bad_lon > 0:
                raise ValidationError(f"Range check failed: {bad_lat} lat and {bad_lon} lon outside NYC boundaries.")
    return True

def run_quality_gate(df: pd.DataFrame, min_pass_rate: float = 0.95, metrics_path: str = None) -> dict:
    """
    Evaluates row-level validity against all constraints and writes metrics.json.
    Raises QualityGateError if pass rate falls below min_pass_rate.
    
    Parameters:
        df (pd.DataFrame): Dataframe to validate.
        min_pass_rate (float): Minimum required pass rate (default: 0.95).
        metrics_path (str): Destination path for metrics.json.
        
    Returns:
        dict: Data quality metrics dictionary.
        
    Raises:
        QualityGateError: If pass rate < min_pass_rate.
    """
    total_rows = len(df)
    if total_rows == 0:
        raise QualityGateError("Quality gate failed: input dataframe is empty.")
        
    is_unique = df["unique_key"].is_unique if "unique_key" in df.columns else False
    dup_keys = int(df["unique_key"].duplicated().sum()) if "unique_key" in df.columns else total_rows
    
    critical_cols = ["unique_key", "created_date", "complaint_type", "borough"]
    existing_crit = [c for c in critical_cols if c in df.columns]
    null_rows = df[existing_crit].isnull().any(axis=1)
    
    if "resolution_hours" in df.columns:
        neg_rows = (df["resolution_hours"] < 0).fillna(False)
    else:
        neg_rows = pd.Series([False] * total_rows, index=df.index)
        
    if "latitude" in df.columns and "longitude" in df.columns:
        has_coords = df["latitude"].notna() & df["longitude"].notna()
        bad_coords = has_coords & (
            (df["latitude"] < 40.48) | (df["latitude"] > 40.95) |
            (df["longitude"] < -74.30) | (df["longitude"] > -73.65)
        )
    else:
        bad_coords = pd.Series([False] * total_rows, index=df.index)
        
    failed_rows = null_rows | neg_rows | bad_coords
    passing_rows = int((~failed_rows).sum())
    pass_rate = round(passing_rows / total_rows, 4)
    
    metrics = {
        "dataset_name": "NYC 311 Service Requests (2010 - 2019)",
        "author": "Dilawar khan (TRN-2026-000961)",
        "date": "17 Nov 2026",
        "total_records": total_rows,
        "passing_records": passing_rows,
        "failed_records": int(total_rows - passing_rows),
        "validation_pass_rate": pass_rate,
        "min_pass_rate_threshold": min_pass_rate,
        "primary_key_unique": bool(is_unique),
        "duplicate_primary_keys": dup_keys,
        "critical_null_violations": int(null_rows.sum()),
        "negative_duration_violations": int(neg_rows.sum()),
        "out_of_bounds_coordinate_violations": int(bad_coords.sum()),
        "open_tickets_count": int(df["closed_date"].isnull().sum()) if "closed_date" in df.columns else 0,
        "quality_gate_passed": bool(pass_rate >= min_pass_rate)
    }
    
    if metrics_path:
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
            
    if pass_rate < min_pass_rate:
        raise QualityGateError(
            f"QUALITY GATE BREACHED: Pass rate {pass_rate*100:.2f}% is below {min_pass_rate*100:.1f}% threshold. "
            f"Failed rows: {metrics['failed_records']}/{total_rows}."
        )
        
    return metrics
