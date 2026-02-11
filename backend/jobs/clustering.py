"""
User Clustering  –  Unsupervised ML
====================================
Groups users into career-focused clusters based on their skill vectors
(from ``assessments.UserSkillScore``).

Uses **KMeans** on a per-user skill-proficiency vector.  Each cluster is
assigned a human-readable label derived from the centroid's dominant skills.

Public API
----------
    from jobs.clustering import get_user_cluster, fit_clusters

    # Refit clusters (run periodically or after many users sign up)
    fit_clusters()

    # Get a single user's cluster info
    info = get_user_cluster(user_id)
    # → {"cluster": 2, "label": "Backend-focused", "centroid_skills": [...]}
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cluster cache key and default TTL (1 hour)
_CACHE_KEY_MODEL = "user_clustering_model"
_CACHE_TTL = 3600

# Default number of clusters
DEFAULT_K = 5

# Human-readable labels mapped to skill-set heuristics
_LABEL_HEURISTICS = [
    ({"python", "django", "flask", "sql", "postgresql", "mongodb", "rest", "api"},
     "Backend-focused"),
    ({"react", "angular", "vue", "javascript", "typescript", "html", "css", "frontend"},
     "Frontend-focused"),
    ({"python", "machine learning", "data science", "tensorflow", "pandas", "numpy", "deep learning", "ai"},
     "Data / ML-focused"),
    ({"aws", "docker", "kubernetes", "ci/cd", "linux", "devops", "terraform", "cloud"},
     "DevOps / Cloud-focused"),
    ({"java", "spring", "c++", "c#", ".net", "microservices"},
     "Enterprise / Systems-focused"),
    ({"figma", "ui", "ux", "design", "adobe", "sketch", "wireframe"},
     "Design-focused"),
    ({"project management", "agile", "scrum", "leadership", "communication"},
     "Management-focused"),
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _build_skill_matrix():
    """
    Build a (num_users × num_skills) matrix from UserSkillScore.

    Returns
    -------
    user_ids : list[int]
    skill_names : list[str]
    X : np.ndarray of shape (n_users, n_skills)
    """
    from assessments.models import UserSkillScore

    scores = (
        UserSkillScore.objects
        .select_related("skill")
        .values_list("user_id", "skill__name", "verified_level")
    )

    if not scores:
        return [], [], np.empty((0, 0))

    # Collect unique users and skills
    user_set: dict[int, dict[str, float]] = {}
    skill_set: set[str] = set()

    for uid, sname, vlevel in scores:
        sname_lower = sname.lower().strip()
        skill_set.add(sname_lower)
        user_set.setdefault(uid, {})[sname_lower] = float(vlevel)

    user_ids = sorted(user_set.keys())
    skill_names = sorted(skill_set)
    skill_idx = {s: i for i, s in enumerate(skill_names)}

    X = np.zeros((len(user_ids), len(skill_names)), dtype=np.float32)
    for row, uid in enumerate(user_ids):
        for sname, level in user_set[uid].items():
            X[row, skill_idx[sname]] = level

    return user_ids, skill_names, X


def _label_for_centroid(centroid: np.ndarray, skill_names: list[str]) -> str:
    """
    Assign a human-readable label to a cluster centroid by finding which
    heuristic skill-set has the highest average value in the centroid.
    """
    # Build {skill_name: centroid_value} map
    skill_vals = {skill_names[i]: float(centroid[i]) for i in range(len(skill_names))}

    best_label = "General"
    best_score = -1.0

    for keywords, label in _LABEL_HEURISTICS:
        # Average centroid value for the keywords that exist in our skill set
        matching = [skill_vals.get(k, 0.0) for k in keywords if k in skill_vals]
        if matching:
            avg = sum(matching) / len(matching)
            if avg > best_score:
                best_score = avg
                best_label = label

    return best_label


def fit_clusters(k: int = DEFAULT_K) -> dict:
    """
    (Re)fit KMeans clustering on all users with verified skill scores.

    Parameters
    ----------
    k : int – number of clusters (default 5, auto-reduced if fewer users).

    Returns
    -------
    dict with keys:
        n_users, n_skills, k, labels (dict user_id→cluster_id),
        cluster_info (list of {id, label, size, top_skills}).
    """
    from sklearn.cluster import KMeans

    user_ids, skill_names, X = _build_skill_matrix()

    if len(user_ids) < 2:
        logger.info("Not enough users for clustering (%d).", len(user_ids))
        return {"n_users": len(user_ids), "k": 0, "labels": {}, "cluster_info": []}

    # Auto-reduce k if we have fewer users than requested clusters
    actual_k = min(k, len(user_ids))

    kmeans = KMeans(n_clusters=actual_k, random_state=42, n_init=10, max_iter=300)
    cluster_labels = kmeans.fit_predict(X)

    # Build result
    user_labels: Dict[int, int] = {}
    for idx, uid in enumerate(user_ids):
        user_labels[uid] = int(cluster_labels[idx])

    cluster_info: list[dict] = []
    for ci in range(actual_k):
        centroid = kmeans.cluster_centers_[ci]
        label = _label_for_centroid(centroid, skill_names)
        # Top skills for this cluster (highest centroid values)
        top_indices = np.argsort(centroid)[::-1][:5]
        top_skills = [
            {"skill": skill_names[i], "avg_level": round(float(centroid[i]), 2)}
            for i in top_indices
            if centroid[i] > 0
        ]
        size = int(np.sum(cluster_labels == ci))
        cluster_info.append({
            "id": ci,
            "label": label,
            "size": size,
            "top_skills": top_skills,
        })

    result = {
        "n_users": len(user_ids),
        "n_skills": len(skill_names),
        "k": actual_k,
        "labels": user_labels,
        "cluster_info": cluster_info,
    }

    # Cache the model output
    cache.set(_CACHE_KEY_MODEL, result, _CACHE_TTL)
    return result


def get_user_cluster(user_id: int) -> dict:
    """
    Return the cluster assignment and label for a single user.

    If clustering hasn't been run or the user has no scores, returns a
    fallback dict with ``cluster="unknown"``.

    Returns
    -------
    dict – {"cluster": int, "label": str, "top_skills": [...]}
    """
    model = cache.get(_CACHE_KEY_MODEL)

    if model is None:
        # Try to fit on the fly (cheap for < 1 000 users)
        try:
            model = fit_clusters()
        except Exception as exc:
            logger.warning("Clustering failed: %s", exc)
            return {"cluster": "unknown", "label": "Not yet classified", "top_skills": []}

    labels = model.get("labels", {})
    cluster_id = labels.get(user_id)

    if cluster_id is None:
        return {"cluster": "unknown", "label": "Not yet classified", "top_skills": []}

    # Find the matching cluster_info entry
    for ci in model.get("cluster_info", []):
        if ci["id"] == cluster_id:
            return {
                "cluster": cluster_id,
                "label": ci["label"],
                "top_skills": ci["top_skills"],
            }

    return {"cluster": cluster_id, "label": "Cluster #" + str(cluster_id), "top_skills": []}
