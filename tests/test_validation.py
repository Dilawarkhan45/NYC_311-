# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
Unit tests for data validation functions in src/validate.py (Part A).
Tests:
- validate_uniqueness
- validate_types
- validate_null_constraints
- validate_ranges
- run_quality_gate (Passing on clean data & failing loudly on corrupted data)
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
    """Provides a valid, clean sample dataset matching schema constraints."""
    return pd.DataFrame({
        "unique_key": [1001, 1002, 1003, 1004],
        "created_date": pd.to_datetime([
            "2015-06-01 08:00:00",
            "2015-06-01 09:00:00",
            "2015-06-01 10:00:00",
            "2015-06-01 11:00:00"
        ]),
        "closed_date": pd.to_datetime([
            "2015-06-01 12:00:00",
            "2015-06-01 14:00:00",
            "2015-06-01 18:00:00",
            "2015-06-02 11:00:00"
        ]),
        "complaint_type": ["HEAT/HOT WATER", "ILLEGAL PARKING", "NOISE - RESIDENTIAL", "STREET CONDITION"],
        "borough": ["BROOKLYN", "MANHATTAN", "QUEENS", "BRONX"],
        "resolution_hours": [4.0, 5.0, 8.0, 24.0],
        "latitude": [40.6782, 40.7831, 40.7282, 40.8448],
        "longitude": [-73.9442, -73.9712, -73.7949, -73.8648]
    })

def test_validate_uniqueness_pass(valid_dataset):
    """Verifies that unique primary keys pass."""
    assert validate_uniqueness(valid_dataset, "unique_key") is True

def test_validate_uniqueness_fail(valid_dataset):
    """Verifies that duplicate primary keys raise ValidationError."""
    corrupted = valid_dataset.copy()
    corrupted.loc[1, "unique_key"] = corrupted.loc[0, "unique_key"]
    with pytest.raises(ValidationError, match="Uniqueness check failed"):
        validate_uniqueness(corrupted, "unique_key")

def test_validate_types_pass(valid_dataset):
    """Verifies that compliant types pass."""
    assert validate_types(valid_dataset) is True

def test_validate_types_fail(valid_dataset):
    """Verifies that non-numeric primary key raises ValidationError."""
    corrupted = valid_dataset.copy()
    corrupted["unique_key"] = ["k1", "k2", "k3", "k4"]
    with pytest.raises(ValidationError, match="Type check failed"):
        validate_types(corrupted)

def test_validate_null_constraints_pass(valid_dataset):
    """Verifies that zero nulls in critical columns passes."""
    assert validate_null_constraints(valid_dataset) is True

def test_validate_null_constraints_fail(valid_dataset):
    """Verifies that null in critical column raises ValidationError."""
    corrupted = valid_dataset.copy()
    corrupted.loc[0, "borough"] = np.nan
    with pytest.raises(ValidationError, match="Null constraint violated"):
        validate_null_constraints(corrupted)

def test_validate_ranges_pass(valid_dataset):
    """Verifies that valid coordinates and non-negative durations pass."""
    assert validate_ranges(valid_dataset) is True

def test_validate_ranges_negative_duration(valid_dataset):
    """Verifies that negative resolution hours raise ValidationError."""
    corrupted = valid_dataset.copy()
    corrupted.loc[0, "resolution_hours"] = -5.0
    with pytest.raises(ValidationError, match="negative resolution hours"):
        validate_ranges(corrupted)

def test_validate_ranges_bad_coordinates(valid_dataset):
    """Verifies that coordinates outside NYC raise ValidationError."""
    corrupted = valid_dataset.copy()
    corrupted.loc[0, "latitude"] = 52.5200 # Berlin latitude
    with pytest.raises(ValidationError, match="outside NYC boundaries"):
        validate_ranges(corrupted)

def test_quality_gate_passes_on_valid_data(valid_dataset, tmp_path):
    """Verifies that clean data passes Quality Gate (100% >= 95% threshold)."""
    metrics_file = tmp_path / "metrics.json"
    result = run_quality_gate(valid_dataset, min_pass_rate=0.95, metrics_path=str(metrics_file))
    assert result["quality_gate_passed"] is True
    assert result["validation_pass_rate"] == 1.0
    assert metrics_file.exists()

def test_quality_gate_fails_loudly_on_corrupted_data(valid_dataset, tmp_path):
    """Verifies that corrupted data breaches threshold and raises QualityGateError loudly."""
    corrupted = valid_dataset.copy()
    corrupted.loc[0, "resolution_hours"] = -10.0
    corrupted.loc[1, "borough"] = np.nan
    metrics_file = tmp_path / "corrupted_metrics.json"
    
    with pytest.raises(QualityGateError, match="QUALITY GATE BREACHED"):
        run_quality_gate(corrupted, min_pass_rate=0.95, metrics_path=str(metrics_file))
        
    assert metrics_file.exists()
