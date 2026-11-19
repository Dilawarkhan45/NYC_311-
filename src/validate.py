# Name: Warisha / Data Engineering Student
# Roll Number: 2026-DS-0142
# Date: November 19, 2026

"""
Data Validation Module for NYC 311 Service Requests.
Implements rigorous, testable validation checks:
- Type validations
- Uniqueness validations
- Null constraint validations
- Value and range boundary validations
- Quality Gate enforcement with automated metrics.json logging
"""

import os
import json
import pandas as pd
import numpy as np

class ValidationError(Exception):
    """Raised when a dataset fails an essential validation check."""
    pass

class QualityGateError(Exception):
    """Raised when data quality pass rate breaches the required quality gate threshold."""
    pass

def validate_uniqueness(df: pd.DataFrame, primary_key: str = "unique_key") -> bool:
    """
    Validates that the specified primary key contains no duplicate values.
    
    Parameters:
        df (pd.DataFrame): Dataset to validate.
        primary_key (str): Primary key column name.
        
    Returns:
        bool: True if strictly unique.
        
    Raises:
        ValidationError: If duplicates exist in the primary key.
    """
    if primary_key not in df.columns:
        raise ValidationError(f"Primary key column '{primary_key}' is missing from dataframe.")
    duplicates = df[primary_key].duplicated().sum()
    if duplicates > 0:
        raise ValidationError(f"Uniqueness validation failed: found {duplicates} duplicate values in '{primary_key}'.")
    return True

def validate_types(df: pd.DataFrame) -> bool:
    """
    Validates that critical columns conform to expected data types.
    
    Parameters:
        df (pd.DataFrame): Dataset to validate.
        
    Returns:
        bool: True if type constraints pass.
        
    Raises:
        ValidationError: If type mismatch occurs.
    """
    if "unique_key" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["unique_key"]):
            raise ValidationError("Type validation failed: 'unique_key' must be numeric.")
            
    for date_col in ["created_date", "closed_date"]:
        if date_col in df.columns and not df[date_col].dropna().empty:
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                raise ValidationError(f"Type validation failed: '{date_col}' must be a datetime dtype.")
                
    for num_col in ["latitude", "longitude"]:
        if num_col in df.columns and not df[num_col].dropna().empty:
            if not pd.api.types.is_float_dtype(df[num_col]):
                raise ValidationError(f"Type validation failed: '{num_col}' must be a float dtype.")
    return True

def validate_null_constraints(df: pd.DataFrame, critical_cols: list = None) -> bool:
    """
    Validates that essential business columns have zero missing values.
    
    Parameters:
        df (pd.DataFrame): Dataset to validate.
        critical_cols (list): List of column names that must never be null.
        
    Returns:
        bool: True if null constraints are satisfied.
        
    Raises:
        ValidationError: If null values are present in critical fields.
    """
    if critical_cols is None:
        critical_cols = ["unique_key", "created_date", "complaint_type", "borough"]
        
    for col in critical_cols:
        if col not in df.columns:
            raise ValidationError(f"Critical column '{col}' missing for null validation.")
        null_count = df[col].isnull().sum()
        if null_count > 0:
            raise ValidationError(f"Null constraint failed: column '{col}' has {null_count} null entries.")
    return True

def validate_ranges(df: pd.DataFrame) -> bool:
    """
    Validates boundary constraints:
    - Coordinates are within the greater NYC area bounds
    - Resolution duration is non-negative
    
    Parameters:
        df (pd.DataFrame): Dataset to validate.
        
    Returns:
        bool: True if range constraints pass.
        
    Raises:
        ValidationError: If values breach defined ranges.
    """
    if "resolution_time_hours" in df.columns:
        invalid_duration = (df["resolution_time_hours"] < 0).sum()
        if invalid_duration > 0:
            raise ValidationError(f"Range check failed: found {invalid_duration} records with negative resolution times.")
            
    if "latitude" in df.columns and "longitude" in df.columns:
        coords_mask = df["latitude"].notna() & df["longitude"].notna()
        if coords_mask.any():
            invalid_lat = ((df.loc[coords_mask, "latitude"] < 40.48) | (df.loc[coords_mask, "latitude"] > 40.95)).sum()
            invalid_lon = ((df.loc[coords_mask, "longitude"] < -74.30) | (df.loc[coords_mask, "longitude"] > -73.65)).sum()
            if invalid_lat > 0 or invalid_lon > 0:
                raise ValidationError(f"Range check failed: {invalid_lat} lat and {invalid_lon} lon outside NYC boundaries.")
    return True

def run_quality_gate(df: pd.DataFrame, min_pass_rate: float = 0.95, metrics_path: str = None) -> dict:
    """
    Executes all validation tests, computes row-level pass rate, logs data-quality metrics,
    and raises QualityGateError loudly if pass rate falls below the minimum required threshold.
    
    Parameters:
        df (pd.DataFrame): Dataframe to validate.
        min_pass_rate (float): Minimum acceptable quality pass rate (default 0.95 / 95%).
        metrics_path (str): Filepath to save metrics.json.
        
    Returns:
        dict: Summary of validation check results and metrics.
        
    Raises:
        QualityGateError: If total pass rate < min_pass_rate.
    """
    total_rows = len(df)
    if total_rows == 0:
        raise QualityGateError("Quality gate failed: input dataframe is empty (0 rows).")
        
    # Check 1: Key Uniqueness
    is_unique = df["unique_key"].is_unique if "unique_key" in df.columns else False
    dup_keys = int(df["unique_key"].duplicated().sum()) if "unique_key" in df.columns else total_rows
    
    # Check 2: Critical non-null fields
    critical_cols = ["unique_key", "created_date", "complaint_type", "borough"]
    existing_crit = [c for c in critical_cols if c in df.columns]
    null_rows = df[existing_crit].isnull().any(axis=1)
    
    # Check 3: Duration non-negative
    if "resolution_time_hours" in df.columns:
        neg_duration_rows = (df["resolution_time_hours"] < 0).fillna(False)
    else:
        neg_duration_rows = pd.Series([False] * total_rows, index=df.index)
        
    # Check 4: Spatial coordinates within NYC if present
    if "latitude" in df.columns and "longitude" in df.columns:
        has_coords = df["latitude"].notna() & df["longitude"].notna()
        bad_coords = has_coords & (
            (df["latitude"] < 40.48) | (df["latitude"] > 40.95) |
            (df["longitude"] < -74.30) | (df["longitude"] > -73.65)
        )
    else:
        bad_coords = pd.Series([False] * total_rows, index=df.index)
        
    # Combine row-level check failures
    failed_rows_mask = null_rows | neg_duration_rows | bad_coords
    passing_rows = int((~failed_rows_mask).sum())
    pass_rate = round(passing_rows / total_rows, 4)
    
    metrics = {
        "total_records": total_rows,
        "passing_records": passing_rows,
        "failed_records": int(total_rows - passing_rows),
        "validation_pass_rate": pass_rate,
        "min_pass_rate_threshold": min_pass_rate,
        "primary_key_unique": bool(is_unique),
        "duplicate_primary_keys": dup_keys,
        "critical_null_violations": int(null_rows.sum()),
        "negative_duration_violations": int(neg_duration_rows.sum()),
        "out_of_bounds_coordinate_violations": int(bad_coords.sum()),
        "quality_gate_passed": bool(pass_rate >= min_pass_rate)
    }
    
    if metrics_path:
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
            
    if pass_rate < min_pass_rate:
        raise QualityGateError(
            f"QUALITY GATE BREACHED: Validation pass rate {pass_rate*100:.2f}% "
            f"is below required threshold of {min_pass_rate*100:.1f}%. "
            f"Failed records: {metrics['failed_records']}/{total_rows}."
        )
        
    return metrics
