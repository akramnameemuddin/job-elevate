"""
Singleton prediction service for the Job-Candidate Fit model.

Usage
-----
    from ml.predictor import JobFitPredictor

    predictor = JobFitPredictor.get_instance()
    score = predictor.predict(user, job)        # 0.0 – 1.0  or  -1.0 if unavailable
    scores = predictor.predict_batch([(u1,j1), (u2,j2)])
"""

import logging
import threading
from pathlib import Path

import joblib
import numpy as np

from .feature_engineering import FEATURE_NAMES, extract_features

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent / 'saved_models'
MODEL_PATH = MODEL_DIR / 'job_fit_model.joblib'
SCALER_PATH = MODEL_DIR / 'feature_scaler.joblib'


class JobFitPredictor:
    """Thread-safe singleton that loads the persisted model and predicts."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.model = None
        self.scaler = None
        self._loaded = False

    # ── Singleton accessor ────────────────────────────────────────
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── Model lifecycle ───────────────────────────────────────────
    def load(self):
        """Load model + scaler from disk.  Returns True on success."""
        if self._loaded:
            return True
        if not MODEL_PATH.exists() or not SCALER_PATH.exists():
            logger.warning(
                "ML model files not found.  Run:  python manage.py train_fit_model"
            )
            return False
        try:
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            self._loaded = True
            logger.info("Job-Fit ML model loaded from %s", MODEL_PATH)
            return True
        except Exception as exc:
            logger.error("Failed to load ML model: %s", exc)
            return False

    def reload(self):
        """Force re-load after retraining."""
        self._loaded = False
        self.model = self.scaler = None
        return self.load()

    @property
    def is_ready(self):
        return self._loaded

    # ── Prediction ────────────────────────────────────────────────
    def predict(self, user, job, user_skill_scores=None, assessment_attempts=None):
        """
        Return the probability (0.0 – 1.0) that *user* is a good fit
        for *job*, or **-1.0** if the model is unavailable.
        """
        if not self._loaded and not self.load():
            return -1.0
        try:
            feat = extract_features(user, job, user_skill_scores, assessment_attempts)
            X = np.array([[feat[n] for n in FEATURE_NAMES]])
            X_s = self.scaler.transform(X)
            return float(self.model.predict_proba(X_s)[0][1])
        except Exception as exc:
            logger.error("Prediction error: %s", exc)
            return -1.0

    def predict_batch(self, pairs, scores_map=None, attempts_map=None):
        """
        Predict for a list of ``(user, job)`` tuples.

        Parameters
        ----------
        pairs : list[tuple[User, Job]]
        scores_map : dict[int, list[UserSkillScore]]  – keyed by user.id
        attempts_map : dict[int, list[AssessmentAttempt]] – keyed by user.id

        Returns
        -------
        list[float]  – same length as *pairs*
        """
        if not self._loaded and not self.load():
            return [-1.0] * len(pairs)
        try:
            rows = []
            for user, job in pairs:
                sc = (scores_map or {}).get(user.id)
                at = (attempts_map or {}).get(user.id)
                feat = extract_features(user, job, sc, at)
                rows.append([feat[n] for n in FEATURE_NAMES])
            X = np.array(rows)
            X_s = self.scaler.transform(X)
            probs = self.model.predict_proba(X_s)[:, 1]
            return [float(p) for p in probs]
        except Exception as exc:
            logger.error("Batch prediction error: %s", exc)
            return [-1.0] * len(pairs)
