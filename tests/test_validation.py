# Name: Warisha / Data Engineering Student
# Roll Number: 2026-DS-0142
# Date: November 19, 2026

"""
Unit tests for data validation functions in src/validate.py.
Tests:
- validate_uniqueness
- validate_types
- validate_null_constraints
- validate_ranges
- run_quality_gate (Bonus challenge: test passing on clean data & failing loudly on corrupted data)
"""

import pytest
import pandas as pd
import numpy as np
from src.validate import (
    validate_uniqueness,
    validate_types,
    validate_null_constraints,
    validate_ranges,
    run_quality_gate,
    ValidationError,
    QualityGateError
)

@pytest.fixture
def valid_dataset():
    """Provides a valid, clean sample dataset that passes all checks."""
    return pd.DataFrame({
        "unique_key": [1001, 1002, 1003, 1004],
        "created_date": pd.to_datetime([
            "2019-12-01 08:00:00",
            "2019-12-01 09:00:00",
            "2019-12-01 10:00:00",
            "2019-12-01 11:00:00"
        ]),
        "closed_date": pd.to_datetime([
            "2019-12-01 12:00:00",
            "2019-12-01 14:00:00",
            "2019-12-01 18:00:00",
            "2019-12-02 11:00:00"
        ]),
        "complaint_type": ["HEAT/HOT WATER", "ILLEGAL PARKING", "NOISE - RESIDENTIAL", "STREET CONDITION"],
        "borough": ["BROOKLYN", "MANHATTAN", "QUEENS", "BRONX"],
        "resolution_time_hours": [4.0, 5.0, 8.0, 24.0],
        "latitude": [40.6782, 40.7831, 40.7282, 40.8448],
        "longitude": [-73.9442, -73.9712, -73.7949, -73.8648]
    })

def test_validate_uniqueness_pass(valid_dataset):
    """Verifies that unique primary keys pass without exception."""
    assert validate_uniqueness(valid_dataset, "unique_key") is True

def test_validate_uniqueness_fail(valid_dataset):
    """Verifies that duplicate keys raise ValidationError."""
    corrupted = valid_dataset.copy()
    corrupted.loc[1, "unique_key"] = corrupted.loc[0, "unique_key"]
    with pytest.raises(ValidationError, match="Uniqueness validation failed"):
        validate_uniqueness(corrupted, "unique_key")

def test_validate_types_pass(valid_dataset):
    """Verifies that valid types pass."""
    assert validate_types(valid_dataset) is True

def test_validate_types_fail(valid_dataset):
    """Verifies that mismatched types raise ValidationError."""
    corrupted = valid_dataset.copy()
    corrupted["unique_key"] = ["id_1", "id_2", "id_3", "id_4"] # Non-numeric
    with pytest.raises(ValidationError, match="Type validation failed"):
        validate_types(corrupted)

def test_validate_null_constraints_pass(valid_dataset):
    """Verifies that zero nulls in critical columns passes."""
    assert validate_null_constraints(valid_dataset) is True

def test_validate_null_constraints_fail(valid_dataset):
    """Verifies that nulls in critical columns raise ValidationError."""
    corrupted = valid_dataset.copy()
    corrupted.loc[0, "borough"] = np.nan
    with pytest.raises(ValidationError, match="Null constraint failed"):
        validate_null_constraints(corrupted)

def test_validate_ranges_pass(valid_dataset):
    """Verifies valid coordinates and positive durations pass."""
    assert validate_ranges(valid_dataset) is True

def test_validate_ranges_negative_duration(valid_dataset):
    """Verifies negative durations raise ValidationError."""
    corrupted = valid_dataset.copy()
    corrupted.loc[0, "resolution_time_hours"] = -5.0
    with pytest.raises(ValidationError, match="negative resolution times"):
        validate_ranges(corrupted)

def test_validate_ranges_bad_coordinates(valid_dataset):
    """Verifies coordinates outside NYC raise ValidationError."""
    corrupted = valid_dataset.copy()
    corrupted.loc[0, "latitude"] = 90.0 # North Pole
    with pytest.raises(ValidationError, match="outside NYC boundaries"):
        validate_ranges(corrupted)

def test_quality_gate_passes_on_valid_data(valid_dataset, tmp_path):
    """Verifies that clean data easily passes quality gate threshold of 95%."""
    metrics_file = tmp_path / "metrics.json"
    result = run_quality_gate(valid_dataset, min_pass_rate=0.95, metrics_path=str(metrics_file))
    assert result["quality_gate_passed"] is True
    assert result["validation_pass_rate"] == 1.0
    assert metrics_file.exists()

def test_quality_gate_fails_loudly_on_corrupted_data(valid_dataset, tmp_path):
    """
    Bonus Challenge Test:
    Verifies that a deliberately corrupted dataset with high error rate
    triggers QualityGateError loudly and writes metrics.json.
    """
    corrupted = valid_dataset.copy()
    # Corrupt 50% of the dataset
    corrupted.loc[0, "resolution_time_hours"] = -10.0 # Negative duration
    corrupted.loc[1, "borough"] = np.nan              # Missing critical field
    metrics_file = tmp_path / "corrupted_metrics.json"
    
    with pytest.raises(QualityGateError, match="QUALITY GATE BREACHED"):
        run_quality_gate(corrupted, min_pass_rate=0.95, metrics_path=str(metrics_file))
        
    assert metrics_file.exists()
