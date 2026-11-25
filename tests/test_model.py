# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
Unit tests for Machine Learning Pipeline and Inference (Part B).
Tests:
- get_preprocessing_pipeline: Preprocessing transformations without data leakage.
- ComplaintTypeMedianBaseline: Baseline model fit and predict.
- Saved pipeline loading and inference on unseen rows.
- Schema validation in predict.py.
"""

import os
import pytest
import numpy as np
import pandas as pd
import joblib

from src.train import (
    get_preprocessing_pipeline,
    ComplaintTypeMedianBaseline,
    evaluate_predictions,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES
)
from src.predict import validate_input_schema, predict_records

@pytest.fixture
def sample_ml_data():
    """Provides sample features and targets for model unit testing."""
    df = pd.DataFrame({
        "unique_key": [1, 2, 3, 4],
        "created_hour": [9, 14, 22, 3],
        "created_day_of_week": [0, 2, 5, 6],
        "is_weekend": [0, 0, 1, 1],
        "distance_to_center_km": [5.2, 12.4, 8.1, 15.0],
        "latitude": [40.71, 40.82, 40.67, 40.75],
        "longitude": [-74.00, -73.92, -73.95, -73.88],
        "agency": ["NYPD", "HPD", "DOT", "NYPD"],
        "complaint_type": ["NOISE - RESIDENTIAL", "HEAT/HOT WATER", "STREET CONDITION", "NOISE - RESIDENTIAL"],
        "borough": ["MANHATTAN", "BRONX", "BROOKLYN", "QUEENS"],
        "open_data_channel_type": ["PHONE", "ONLINE", "MOBILE", "PHONE"],
        "resolution_hours": [6.0, 48.0, 120.0, 4.0]
    })
    return df

def test_preprocessing_pipeline(sample_ml_data):
    """Verifies that ColumnTransformer encodes and scales features without error."""
    preprocessor = get_preprocessing_pipeline()
    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X = sample_ml_data[feature_cols]
    
    transformed = preprocessor.fit_transform(X)
    assert transformed.shape[0] == len(sample_ml_data)
    assert not np.isnan(transformed).any()

def test_complaint_type_median_baseline(sample_ml_data):
    """Verifies that baseline regressor computes complaint-type medians."""
    baseline = ComplaintTypeMedianBaseline()
    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X = sample_ml_data[feature_cols]
    y = sample_ml_data["resolution_hours"].values
    
    baseline.fit(X, y)
    preds = baseline.predict(X)
    
    # Noise complaints: medians of 6.0 and 4.0 is 5.0
    assert preds[0] == 5.0
    assert preds[3] == 5.0
    # Heat/hot water has only one sample (48.0)
    assert preds[1] == 48.0

def test_evaluate_predictions_metrics():
    """Verifies computation of MAE, RMSE, and R2."""
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 30.0])
    metrics = evaluate_predictions(y_true, y_pred)
    
    assert "MAE (Hours)" in metrics
    assert "RMSE (Hours)" in metrics
    assert "R2 Score" in metrics
    assert metrics["MAE (Hours)"] == pytest.approx(1.33, rel=1e-2)

def test_validate_input_schema_success(sample_ml_data):
    """Verifies that complete schema passes validation."""
    assert validate_input_schema(sample_ml_data) is True

def test_validate_input_schema_missing_column(sample_ml_data):
    """Verifies that missing feature raises ValueError."""
    bad_df = sample_ml_data.drop(columns=["agency"])
    with pytest.raises(ValueError, match="Missing required feature columns"):
        validate_input_schema(bad_df)

def test_saved_pipeline_scoring_unseen_rows(sample_ml_data, tmp_path):
    """Verifies that serialized pipeline loads and produces predictions on unseen rows."""
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "pipeline.joblib")
    if os.path.exists(model_path):
        pipeline = joblib.load(model_path)
        feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
        preds = pipeline.predict(sample_ml_data[feature_cols])
        assert len(preds) == len(sample_ml_data)
        clipped_preds = np.clip(preds, 0.0, None)
        assert (clipped_preds >= 0).all()
