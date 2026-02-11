"""
Dataset builder for the Job-Candidate Fit model.

Provides two data sources:
  1. Real data  – mined from Application records with known outcomes
  2. Synthetic  – generated with domain-knowledge rules + noise

The two are blended so the model has at least `min_samples` rows
even when production data is sparse.
"""

import logging

import numpy as np

from .feature_engineering import FEATURE_NAMES, N_FEATURES, extract_features

logger = logging.getLogger(__name__)

# ── Label mapping (only definitive outcomes) ──────────────────────
STATUS_LABEL = {
    'Hired': 1,
    'Offered': 1,
    'Interview': 1,
    'Shortlisted': 1,
    'Rejected': 0,
    # 'Applied' is excluded — outcome still unknown
}


# ══════════════════════════════════════════════════════════════════
#  Real data
# ══════════════════════════════════════════════════════════════════

def build_from_applications():
    """
    Build (X, y) from Application records whose status is not 'Applied'.

    Returns
    -------
    X : ndarray (n, 23)
    y : ndarray (n,)
    n : int  – number of real samples
    """
    from recruiter.models import Application
    from assessments.models import AssessmentAttempt, UserSkillScore

    apps = (
        Application.objects
        .exclude(status='Applied')
        .select_related('job', 'applicant')
    )

    X_rows, y_rows = [], []
    for app in apps:
        label = STATUS_LABEL.get(app.status)
        if label is None:
            continue
        user = app.applicant
        job = app.job
        scores = list(UserSkillScore.objects.filter(user=user).select_related('skill'))
        attempts = list(AssessmentAttempt.objects.filter(user=user))
        feat = extract_features(user, job, scores, attempts)
        X_rows.append([feat[n] for n in FEATURE_NAMES])
        y_rows.append(label)

    if not X_rows:
        return np.zeros((0, N_FEATURES)), np.array([]), 0
    return np.array(X_rows, dtype=np.float64), np.array(y_rows, dtype=np.float64), len(X_rows)


# ══════════════════════════════════════════════════════════════════
#  Synthetic data
# ══════════════════════════════════════════════════════════════════

def generate_synthetic(n_samples=500, random_state=42):
    """
    Generate synthetic training data whose labels follow domain rules:

    * High skill-match + good proficiency + experience fit  → likely positive
    * Missing mandatory skills / large proficiency gaps      → likely negative
    * Overconfidence (self-rated >> verified)                → mild negative
    * Richer profile (projects, certs)                       → mild positive

    Gaussian noise is added so the boundary is never perfectly separable —
    this forces the model to *learn* rather than memorize.

    Returns
    -------
    X : ndarray (n_samples, 23)
    y : ndarray (n_samples,)
    """
    rng = np.random.RandomState(random_state)
    X = np.zeros((n_samples, N_FEATURES))

    # ── Feature distributions ─────────────────────────────────────
    # 0  skill_match_ratio
    X[:, 0] = rng.beta(3, 2, n_samples)
    # 1  total_matched_skills
    X[:, 1] = rng.poisson(3, n_samples)
    # 2  total_required_skills
    X[:, 2] = rng.poisson(5, n_samples) + 1
    # 3  missing_mandatory_count
    X[:, 3] = rng.poisson(0.8, n_samples)
    # 4  avg_matched_proficiency
    X[:, 4] = rng.normal(5.5, 2.0, n_samples).clip(0, 10)
    # 5  min_matched_proficiency
    X[:, 5] = rng.normal(4.0, 2.5, n_samples).clip(0, 10)
    # 6  avg_proficiency_gap
    X[:, 6] = rng.exponential(1.5, n_samples).clip(0, 8)
    # 7  max_proficiency_gap
    X[:, 7] = rng.exponential(2.0, n_samples).clip(0, 10)
    # 8  overconfidence_avg
    X[:, 8] = rng.normal(0.5, 1.5, n_samples)
    # 9  experience_delta
    X[:, 9] = rng.normal(0.5, 2.5, n_samples)
    # 10 experience_ratio
    X[:, 10] = rng.lognormal(0.2, 0.5, n_samples).clip(0, 5)
    # 11 meets_experience_req
    X[:, 11] = (X[:, 9] >= 0).astype(float)
    # 12 education_level
    X[:, 12] = rng.choice([1, 2, 3, 4], n_samples, p=[0.10, 0.50, 0.30, 0.10])
    # 13 cgpa_normalized
    X[:, 13] = rng.normal(0.72, 0.12, n_samples).clip(0.3, 1.0)
    # 14 num_projects
    X[:, 14] = rng.poisson(2.5, n_samples)
    # 15 num_certifications
    X[:, 15] = rng.poisson(1.5, n_samples)
    # 16 num_internships
    X[:, 16] = rng.poisson(1.0, n_samples)
    # 17 has_work_experience
    X[:, 17] = rng.binomial(1, 0.45, n_samples)
    # 18 profile_completeness
    X[:, 18] = rng.beta(4, 2, n_samples)
    # 19 assessment_pass_rate
    X[:, 19] = rng.beta(3, 2, n_samples)
    # 20 avg_assessment_score
    X[:, 20] = rng.beta(4, 3, n_samples)
    # 21 num_verified_skills
    X[:, 21] = rng.poisson(2, n_samples)
    # 22 text_similarity
    X[:, 22] = rng.beta(2, 5, n_samples)

    # ── Label generation via logistic model ───────────────────────
    #    Weights encode domain knowledge; noise prevents memorization.
    fit = (
        +0.25 * X[:, 0]                                  # skill_match_ratio
        + 0.15 * (X[:, 4] / 10.0)                        # avg_matched_proficiency
        - 0.20 * np.minimum(X[:, 3] / 3.0, 1.0)          # missing_mandatory_count
        - 0.10 * np.minimum(X[:, 6] / 8.0, 1.0)          # avg_proficiency_gap
        + 0.08 * X[:, 11]                                 # meets_experience_req
        + 0.05 * (X[:, 12] / 4.0)                        # education_level
        + 0.05 * X[:, 13]                                 # cgpa_normalized
        + 0.03 * np.minimum(X[:, 14] / 5.0, 1.0)         # num_projects
        + 0.03 * np.minimum(X[:, 15] / 3.0, 1.0)         # num_certifications
        + 0.04 * X[:, 19]                                 # assessment_pass_rate
        + 0.05 * X[:, 20]                                 # avg_assessment_score
        + 0.05 * X[:, 22]                                 # text_similarity
        - 0.03 * np.minimum(X[:, 8] / 3.0, 1.0)          # overconfidence
        + 0.02 * X[:, 18]                                 # profile_completeness
    )
    fit += rng.normal(0, 0.08, n_samples)                  # noise

    probability = 1.0 / (1.0 + np.exp(-(fit - 0.45) * 12))
    y = rng.binomial(1, probability).astype(np.float64)

    return X, y


# ══════════════════════════════════════════════════════════════════
#  Public entry point
# ══════════════════════════════════════════════════════════════════

def build_dataset(min_samples=100, synthetic_count=500, random_state=42):
    """
    Combine real and synthetic data into one training set.

    Returns
    -------
    X : ndarray
    y : ndarray
    meta : dict  – statistics about the dataset
    """
    try:
        X_real, y_real, n_real = build_from_applications()
    except Exception as exc:
        logger.warning("Could not load real application data: %s", exc)
        X_real = np.zeros((0, N_FEATURES))
        y_real = np.array([])
        n_real = 0

    X_syn, y_syn = generate_synthetic(synthetic_count, random_state)

    if n_real > 0:
        X = np.vstack([X_real, X_syn])
        y = np.concatenate([y_real, y_syn])
    else:
        X = X_syn
        y = y_syn

    meta = {
        'n_real_samples': n_real,
        'n_synthetic_samples': synthetic_count,
        'n_total_samples': len(y),
        'positive_ratio': float(y.mean()) if len(y) else 0.0,
        'feature_names': FEATURE_NAMES,
    }
    logger.info(
        "Dataset ready — %d real + %d synthetic = %d total  (%.1f%% positive)",
        n_real, synthetic_count, len(y), meta['positive_ratio'] * 100,
    )
    return X, y, meta
