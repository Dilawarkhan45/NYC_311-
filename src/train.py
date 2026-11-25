# Name: Dilawar khan
# Roll Number: TRN-2026-000961
# Date: 17 Nov 2026

"""
End-to-End Tabular Machine Learning Module (Part B).
Dataset: NYC Open Data 311 Service Requests (2010 - 2019)

Implements:
1. Leak-free, time-based train/test split:
   - Train: 2010 to 2017 (~80% of rows)
   - Test: 2018 to 2019 (~20% of rows)
2. Scikit-learn Pipeline and ColumnTransformer fitted exclusively on training data.
3. Baseline Model: Complaint-type median regressor.
4. Candidate Models: Ridge Regression and Gradient Boosting Regressor (trained on log(1+hours)).
5. Expanding time-window cross-validation on training set.
6. Metric evaluation in original physical units (Hours): MAE, RMSE, and R-squared.
7. Concrete error analysis across subgroups (Boroughs and Agencies).
8. Pipeline serialization to models/pipeline.joblib.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CLEANED_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "cleaned", "cleaned_311_data.csv")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "outputs", "reports")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "outputs", "figures")

NUMERIC_FEATURES = [
    "created_hour",
    "created_day_of_week",
    "is_weekend",
    "distance_to_center_km",
    "latitude",
    "longitude"
]

CATEGORICAL_FEATURES = [
    "agency",
    "complaint_type",
    "borough",
    "open_data_channel_type"
]

class ComplaintTypeMedianBaseline(BaseEstimator, RegressorMixin):
    """
    Baseline regressor that predicts the training median resolution hours
    for each complaint type, with fallback to overall training median.
    """
    def __init__(self):
        self.median_by_type_ = {}
        self.overall_median_ = 0.0

    def fit(self, X, y):
        df = X.copy()
        df["_target"] = y
        self.overall_median_ = float(np.median(y))
        grouped = df.groupby("complaint_type")["_target"].median()
        self.median_by_type_ = grouped.to_dict()
        return self

    def predict(self, X):
        df = X.copy()
        preds = df["complaint_type"].map(self.median_by_type_).fillna(self.overall_median_)
        return preds.values

def get_preprocessing_pipeline() -> ColumnTransformer:
    """
    Builds a leakage-free preprocessing ColumnTransformer for tabular features.
    
    Returns:
        ColumnTransformer: Preprocessor instance.
    """
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(transformers=[
        ("num", numeric_transformer, NUMERIC_FEATURES),
        ("cat", categorical_transformer, CATEGORICAL_FEATURES)
    ])
    
    return preprocessor

def evaluate_predictions(y_true, y_pred) -> dict:
    """Computes MAE, RMSE, and R2 in original physical units (hours)."""
    # Enforce non-negative predictions
    y_pred_clipped = np.clip(y_pred, 0, None)
    mae = mean_absolute_error(y_true, y_pred_clipped)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred_clipped))
    r2 = r2_score(y_true, y_pred_clipped)
    return {
        "MAE (Hours)": round(mae, 2),
        "RMSE (Hours)": round(rmse, 2),
        "R2 Score": round(r2, 4)
    }

def run_model_training(data_path: str = CLEANED_DATA_PATH):
    """Executes the full Part B machine learning workflow."""
    print("=" * 72)
    print("STARTING TABULAR MACHINE LEARNING PIPELINE (PART B)")
    print("Author: Dilawar khan | Roll: TRN-2026-000961 | Date: 17 Nov 2026")
    print("=" * 72)
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)
    
    df = pd.read_csv(data_path, low_memory=False)
    print(f"Loaded dataset: {len(df):,} total rows.")
    
    # 1. Target Preparation: Exclude active/open requests (missing closed_date)
    closed_mask = df["closed_date"].notna() & df["resolution_hours"].notna()
    closed_df = df[closed_mask].copy()
    print(f"Valid closed tickets for modeling: {len(closed_df):,} rows (excluded {len(df)-len(closed_df):,} open tickets).")
    
    # Ensure created_year is available for time-based split
    if "created_year" not in closed_df.columns:
        closed_df["created_year"] = pd.to_datetime(closed_df["created_date"], format="mixed", errors="coerce").dt.year
    else:
        closed_df["created_year"] = closed_df["created_year"].astype(int)
    
    # 2. Time-Based Train/Test Split (Before Any Fitting)
    # Train: 2010 - 2017 (~80%) | Test: 2018 - 2019 (~20%)
    train_mask = closed_df["created_year"] <= 2017
    test_mask = closed_df["created_year"] >= 2018
    
    train_df = closed_df[train_mask].sort_values("created_date").reset_index(drop=True)
    test_df = closed_df[test_mask].sort_values("created_date").reset_index(drop=True)
    
    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X_train, y_train = train_df[feature_cols], train_df["resolution_hours"].values
    X_test, y_test = test_df[feature_cols], test_df["resolution_hours"].values
    
    print(f"Train set: {len(X_train):,} rows ({len(X_train)/len(closed_df)*100:.1f}%) [Years {train_df['created_year'].min()} - {train_df['created_year'].max()}]")
    print(f"Test set:  {len(X_test):,} rows ({len(X_test)/len(closed_df)*100:.1f}%) [Years {test_df['created_year'].min()} - {test_df['created_year'].max()}]")
    
    # 3. Model 0: Baseline Model (Complaint-Type Median)
    print("\n--- Training Model 0: Complaint-Type Median Baseline ---")
    baseline = ComplaintTypeMedianBaseline()
    baseline.fit(X_train, y_train)
    y_pred_base_train = baseline.predict(X_train)
    y_pred_base_test = baseline.predict(X_test)
    base_eval = evaluate_predictions(y_test, y_pred_base_test)
    print(f"Baseline Test Performance: MAE = {base_eval['MAE (Hours)']}h, RMSE = {base_eval['RMSE (Hours)']}h, R2 = {base_eval['R2 Score']}")
    
    # 4. Model 1: Ridge Regression Pipeline (Trained on log1p(hours))
    print("\n--- Training Model 1: Regularized Ridge Regression ---")
    preprocessor = get_preprocessing_pipeline()
    ridge_reg = TransformedTargetRegressor(
        regressor=Ridge(alpha=10.0),
        func=np.log1p,
        inverse_func=np.expm1
    )
    ridge_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", ridge_reg)
    ])
    ridge_pipeline.fit(X_train, y_train)
    y_pred_ridge_test = ridge_pipeline.predict(X_test)
    ridge_eval = evaluate_predictions(y_test, y_pred_ridge_test)
    print(f"Ridge Test Performance: MAE = {ridge_eval['MAE (Hours)']}h, RMSE = {ridge_eval['RMSE (Hours)']}h, R2 = {ridge_eval['R2 Score']}")
    
    # 5. Model 2: Gradient Boosting Regressor Pipeline (Trained on log1p(hours))
    print("\n--- Training Model 2: HistGradientBoosting Regressor ---")
    preprocessor_gb = get_preprocessing_pipeline()
    gb_reg = TransformedTargetRegressor(
        regressor=HistGradientBoostingRegressor(
            max_iter=150,
            learning_rate=0.08,
            max_depth=6,
            random_state=42
        ),
        func=np.log1p,
        inverse_func=np.expm1
    )
    gb_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor_gb),
        ("regressor", gb_reg)
    ])
    gb_pipeline.fit(X_train, y_train)
    y_pred_gb_test = gb_pipeline.predict(X_test)
    gb_eval = evaluate_predictions(y_test, y_pred_gb_test)
    print(f"Gradient Boosting Test Performance: MAE = {gb_eval['MAE (Hours)']}h, RMSE = {gb_eval['RMSE (Hours)']}h, R2 = {gb_eval['R2 Score']}")
    
    # 6. Expanding Time-Window Cross-Validation (on Training Data Only)
    print("\n--- Running Expanding Time-Window Cross-Validation (Train Split Only) ---")
    tscv = TimeSeriesSplit(n_splits=4)
    cv_scores_ridge = []
    cv_scores_gb = []
    
    for fold, (tr_idx, val_idx) in enumerate(tscv.split(X_train), 1):
        X_tr, y_tr = X_train.iloc[tr_idx], y_train[tr_idx]
        X_va, y_va = X_train.iloc[val_idx], y_train[val_idx]
        
        # Ridge fold
        pipe_r = Pipeline(steps=[("prep", get_preprocessing_pipeline()), ("reg", TransformedTargetRegressor(Ridge(alpha=10.0), func=np.log1p, inverse_func=np.expm1))])
        pipe_r.fit(X_tr, y_tr)
        cv_scores_ridge.append(mean_absolute_error(y_va, np.clip(pipe_r.predict(X_va), 0, None)))
        
        # GB fold
        pipe_gb = Pipeline(steps=[("prep", get_preprocessing_pipeline()), ("reg", TransformedTargetRegressor(HistGradientBoostingRegressor(max_iter=100, random_state=42), func=np.log1p, inverse_func=np.expm1))])
        pipe_gb.fit(X_tr, y_tr)
        cv_scores_gb.append(mean_absolute_error(y_va, np.clip(pipe_gb.predict(X_va), 0, None)))
        
    cv_mae_ridge = round(float(np.mean(cv_scores_ridge)), 2)
    cv_mae_gb = round(float(np.mean(cv_scores_gb)), 2)
    print(f"CV MAE: Ridge = {cv_mae_ridge}h | Gradient Boosting = {cv_mae_gb}h")
    
    # 7. Model Comparison Table
    comparison_df = pd.DataFrame([
        {
            "Model": "Baseline (Complaint-Type Median)",
            "CV MAE (Hours)": "N/A (Heuristic)",
            "Test MAE (Hours)": base_eval["MAE (Hours)"],
            "Test RMSE (Hours)": base_eval["RMSE (Hours)"],
            "Test R2": base_eval["R2 Score"],
            "Pipeline Structure": "Rule-based grouping on training median"
        },
        {
            "Model": "Ridge Regression (log1p)",
            "CV MAE (Hours)": cv_mae_ridge,
            "Test MAE (Hours)": ridge_eval["MAE (Hours)"],
            "Test RMSE (Hours)": ridge_eval["RMSE (Hours)"],
            "Test R2": ridge_eval["R2 Score"],
            "Pipeline Structure": "ColumnTransformer + Ridge(alpha=10.0)"
        },
        {
            "Model": "HistGradientBoosting (log1p)",
            "CV MAE (Hours)": cv_mae_gb,
            "Test MAE (Hours)": gb_eval["MAE (Hours)"],
            "Test RMSE (Hours)": gb_eval["RMSE (Hours)"],
            "Test R2": gb_eval["R2 Score"],
            "Pipeline Structure": "ColumnTransformer + HistGradientBoosting"
        }
    ])
    
    comp_csv = os.path.join(REPORTS_DIR, "model_comparison.csv")
    comparison_df.to_csv(comp_csv, index=False)
    print(f"\n[SUCCESS] Model comparison table saved to: {comp_csv}")
    print("\n" + comparison_df.to_string(index=False) + "\n")
    
    # 8. Save Best Performing Pipeline
    best_pipeline = gb_pipeline if gb_eval["MAE (Hours)"] <= ridge_eval["MAE (Hours)"] else ridge_pipeline
    model_save_path = os.path.join(MODEL_DIR, "pipeline.joblib")
    joblib.dump(best_pipeline, model_save_path)
    print(f"[SUCCESS] Saved fitted end-to-end pipeline to: {model_save_path}")
    
    # 9. Concrete Error Analysis & Residual Plot
    test_eval_df = test_df.copy()
    test_eval_df["predicted_hours"] = np.clip(best_pipeline.predict(X_test), 0, None)
    test_eval_df["residual_hours"] = test_eval_df["resolution_hours"] - test_eval_df["predicted_hours"]
    test_eval_df["abs_error_hours"] = np.abs(test_eval_df["residual_hours"])
    
    # Subgroup error analysis by borough
    borough_error = test_eval_df.groupby("borough")["abs_error_hours"].agg(
        sample_count="count",
        mae_hours="mean",
        median_error_hours="median"
    ).reset_index()
    borough_error.to_csv(os.path.join(REPORTS_DIR, "borough_model_error.csv"), index=False)
    
    # Residual Visualization
    plt.figure(figsize=(10, 5.5))
    plt.scatter(test_eval_df["predicted_hours"], test_eval_df["residual_hours"], alpha=0.35, color="#1f77b4", edgecolor="none", s=25)
    plt.axhline(0, color="red", linestyle="--", linewidth=1.5)
    plt.title("Residual Plot: Resolution Duration (Predicted vs. Residual Hours on Test Set)", fontsize=13, weight="bold", pad=12)
    plt.xlabel("Predicted Resolution Duration (Hours)", fontsize=11, labelpad=8)
    plt.ylabel("Residuals: Actual - Predicted (Hours)", fontsize=11, labelpad=8)
    plt.xlim(0, test_eval_df["predicted_hours"].quantile(0.99))
    plt.tight_layout()
    res_plot_path = os.path.join(FIGURES_DIR, "figure5_residual_plot.png")
    plt.savefig(res_plot_path, dpi=300)
    plt.close()
    print(f"[SUCCESS] Residual plot saved to: {res_plot_path}")
    
    return comparison_df

if __name__ == "__main__":
    run_model_training()
