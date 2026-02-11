"""
Model training & evaluation for Job-Candidate Fit Prediction.

Algorithm : Random Forest Classifier (ensemble of 200 decision trees)
Validation: 5-fold Stratified Cross-Validation
Metric    : F1-score (primary), Accuracy, Precision, Recall, AUC-ROC
"""

import json
import logging
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

from .dataset import build_dataset
from .feature_engineering import FEATURE_NAMES

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────
MODEL_DIR = Path(__file__).resolve().parent / 'saved_models'
MODEL_PATH = MODEL_DIR / 'job_fit_model.joblib'
SCALER_PATH = MODEL_DIR / 'feature_scaler.joblib'
REPORT_PATH = MODEL_DIR / 'training_report.json'


def train_and_evaluate(min_samples=100, synthetic_count=500):
    """
    Full training pipeline.

    1. Build dataset (real Application records + synthetic)
    2. 80/20 stratified train-test split
    3. StandardScaler normalisation
    4. Train Random Forest with 5-fold cross-validation
    5. Evaluate on held-out test set
    6. Save model, scaler, and JSON report

    Returns
    -------
    dict – training report (also written to ``saved_models/training_report.json``)
    """
    t0 = time.time()

    # ── 1. Data ───────────────────────────────────────────────────
    X, y, data_meta = build_dataset(min_samples, synthetic_count)

    # ── 2. Split ──────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42,
    )

    # ── 3. Scale ──────────────────────────────────────────────────
    scaler = StandardScaler()
    X_tr = scaler.fit_transform(X_train)
    X_te = scaler.transform(X_test)

    # ── 4. Train Random Forest ────────────────────────────────────
    model = RandomForestClassifier(
        n_estimators=200,       # 200 decision trees vote together
        max_depth=12,           # max tree depth (prevents overfitting)
        min_samples_split=5,    # min samples to split an internal node
        min_samples_leaf=2,     # min samples at each leaf
        class_weight='balanced',  # auto-handle class imbalance
        random_state=42,
        n_jobs=-1,              # use all CPU cores
    )

    # ── Cross-validation (5-fold) ─────────────────────────────────
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_tr, y_train, cv=cv, scoring='f1')
    logger.info("CV F1 scores: %s  mean=%.4f", cv_scores, cv_scores.mean())

    # ── Train on full training set ────────────────────────────────
    model.fit(X_tr, y_train)

    # ── 5. Evaluate on test set ───────────────────────────────────
    y_pred = model.predict(X_te)
    y_prob = model.predict_proba(X_te)[:, 1]
    cm = confusion_matrix(y_test, y_pred)
    cls_report = classification_report(y_test, y_pred, output_dict=True,
                                       target_names=['Not Fit', 'Good Fit'],
                                       zero_division=0)

    metrics = {
        'accuracy':   round(float(accuracy_score(y_test, y_pred)), 4),
        'precision':  round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        'recall':     round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        'f1_score':   round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        'roc_auc':    round(float(roc_auc_score(y_test, y_prob)), 4),
        'cv_f1_mean': round(float(cv_scores.mean()), 4),
        'cv_f1_std':  round(float(cv_scores.std()), 4),
    }

    # ── Feature importance ────────────────────────────────────────
    importance = {}
    for fname, imp in sorted(
        zip(FEATURE_NAMES, model.feature_importances_), key=lambda x: -x[1]
    ):
        importance[fname] = round(float(imp), 4)

    # ── 6. Persist ────────────────────────────────────────────────
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    elapsed = round(time.time() - t0, 2)

    report = {
        'model_name': 'Random Forest Classifier',
        'n_estimators': 200,
        'training_time_seconds': elapsed,
        'dataset': data_meta,
        'metrics': metrics,
        'confusion_matrix': cm.tolist(),
        'classification_report': cls_report,
        'feature_importance': importance,
        'feature_names': FEATURE_NAMES,
        'model_path': str(MODEL_PATH),
        'scaler_path': str(SCALER_PATH),
    }
    with open(REPORT_PATH, 'w') as fh:
        json.dump(report, fh, indent=2)

    logger.info(
        "Random Forest  F1=%.4f  AUC=%.4f  saved → %s",
        metrics['f1_score'], metrics['roc_auc'], MODEL_PATH,
    )
    return report
