"""
Bhoomi-AI: Model Training Pipeline
====================================
Trains a Random Forest Regressor to predict the optimal
solid urea percentage for a given field condition.

Input Features:
- crop_type, plot_acres, soil_nitrogen, soil_ph,
  organic_carbon, phosphorus, potassium,
  days_since_sowing, ndvi

Output:
- optimal_solid_urea_pct (30-75%)

The Nano urea % = 100 - solid_urea_pct
Actual bags/bottles are calculated from the percentage post-prediction.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import json


def train_model():
    # =====================
    # 1. LOAD DATASET
    # =====================
    print("=" * 60)
    print("BHOOMI-AI MODEL TRAINING")
    print("=" * 60)

    df = pd.read_csv("bhoomi_training_data.csv")
    print(f"\nDataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    # =====================
    # 2. FEATURE ENGINEERING
    # =====================

    # Encode categorical features
    crop_encoder = LabelEncoder()
    df["crop_encoded"] = crop_encoder.fit_transform(df["crop_type"])

    stage_encoder = LabelEncoder()
    df["stage_encoded"] = stage_encoder.fit_transform(df["growth_stage"])

    district_encoder = LabelEncoder()
    df["district_encoded"] = district_encoder.fit_transform(df["district"])

    # Select features for training
    feature_columns = [
        "crop_encoded",
        "plot_acres",
        "soil_nitrogen_kg_ha",
        "soil_ph",
        "organic_carbon_pct",
        "phosphorus_kg_ha",
        "potassium_kg_ha",
        "days_since_sowing",
        "stage_encoded",
        "ndvi",
        "district_encoded",
    ]

    target_column = "optimal_solid_urea_pct"

    X = df[feature_columns]
    y = df[target_column]

    print(f"\nFeatures: {feature_columns}")
    print(f"Target: {target_column}")
    print(f"Target range: {y.min():.1f}% - {y.max():.1f}%")
    print(f"Target mean: {y.mean():.1f}%")

    # =====================
    # 3. TRAIN/TEST SPLIT
    # =====================
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\nTrain set: {X_train.shape[0]} rows")
    print(f"Test set:  {X_test.shape[0]} rows")

    # =====================
    # 4. TRAIN RANDOM FOREST
    # =====================
    print("\nTraining Random Forest...")

    model = RandomForestRegressor(
        n_estimators=150,       # 150 trees
        max_depth=12,           # Prevent overfitting
        min_samples_split=5,    # Minimum samples to split a node
        min_samples_leaf=3,     # Minimum samples in a leaf
        random_state=42,
        n_jobs=-1               # Use all CPU cores
    )

    model.fit(X_train, y_train)
    print("Training complete!")

    # =====================
    # 5. EVALUATE MODEL
    # =====================
    print("\n" + "=" * 60)
    print("MODEL EVALUATION")
    print("=" * 60)

    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    # Training metrics
    print(f"\n--- Training Set ---")
    print(f"MAE:  {mean_absolute_error(y_train, y_pred_train):.2f}%")
    print(f"RMSE: {np.sqrt(mean_squared_error(y_train, y_pred_train)):.2f}%")
    print(f"R²:   {r2_score(y_train, y_pred_train):.4f}")

    # Test metrics
    print(f"\n--- Test Set ---")
    mae = mean_absolute_error(y_test, y_pred_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    r2 = r2_score(y_test, y_pred_test)
    print(f"MAE:  {mae:.2f}%")
    print(f"RMSE: {rmse:.2f}%")
    print(f"R²:   {r2:.4f}")

    # Cross-validation
    print(f"\n--- 5-Fold Cross Validation ---")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="neg_mean_absolute_error")
    print(f"Mean MAE: {-cv_scores.mean():.2f}% (±{cv_scores.std():.2f}%)")

    # =====================
    # 6. FEATURE IMPORTANCE
    # =====================
    print(f"\n--- Feature Importance ---")
    importances = model.feature_importances_
    feature_importance = sorted(
        zip(feature_columns, importances),
        key=lambda x: x[1],
        reverse=True
    )
    for feat, imp in feature_importance:
        bar = "█" * int(imp * 50)
        print(f"  {feat:25s} {imp:.4f} {bar}")

    # =====================
    # 7. SAMPLE PREDICTIONS
    # =====================
    print(f"\n--- Sample Predictions (Test Set) ---")
    print(f"{'Actual':>8s} {'Predicted':>10s} {'Error':>8s}")
    print("-" * 30)
    for i in range(min(15, len(y_test))):
        actual = y_test.iloc[i]
        predicted = y_pred_test[i]
        error = abs(actual - predicted)
        print(f"{actual:8.1f}% {predicted:10.1f}% {error:7.1f}%")

    # =====================
    # 8. EXPORT MODEL & ENCODERS
    # =====================
    print("\n" + "=" * 60)
    print("EXPORTING MODEL")
    print("=" * 60)

    # Save model
    joblib.dump(model, "bhoomi_model.joblib")
    print("Model saved: bhoomi_model.joblib")

    # Save encoders
    joblib.dump(crop_encoder, "crop_encoder.joblib")
    joblib.dump(stage_encoder, "stage_encoder.joblib")
    joblib.dump(district_encoder, "district_encoder.joblib")
    print("Encoders saved: crop_encoder.joblib, stage_encoder.joblib, district_encoder.joblib")

    # Save feature order and encoder mappings for the API
    model_config = {
        "feature_columns": feature_columns,
        "target_column": target_column,
        "crop_classes": dict(zip(
            crop_encoder.classes_.tolist(),
            crop_encoder.transform(crop_encoder.classes_).tolist()
        )),
        "stage_classes": dict(zip(
            stage_encoder.classes_.tolist(),
            stage_encoder.transform(stage_encoder.classes_).tolist()
        )),
        "district_classes": dict(zip(
            district_encoder.classes_.tolist(),
            district_encoder.transform(district_encoder.classes_).tolist()
        )),
        "model_metrics": {
            "test_mae": round(mae, 2),
            "test_rmse": round(rmse, 2),
            "test_r2": round(r2, 4),
            "cv_mean_mae": round(-cv_scores.mean(), 2),
        },
        "n_requirement_kg_ha": {
            "wheat": 120,
            "paddy": 110
        }
    }

    with open("model_config.json", "w") as f:
        json.dump(model_config, f, indent=2)
    print("Config saved: model_config.json")

    print("\n✅ All files exported successfully!")
    print("Files: bhoomi_model.joblib, crop_encoder.joblib,")
    print("       stage_encoder.joblib, district_encoder.joblib,")
    print("       model_config.json")


if __name__ == "__main__":
    train_model()
