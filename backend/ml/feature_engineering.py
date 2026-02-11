"""
Feature engineering for the Job-Candidate Fit Prediction model.

Extracts 23 numerical features from a (User, Job) pair covering:
  - Skill coverage & proficiency
  - Experience fit
  - Education level
  - Profile richness (projects, certs, internships)
  - Assessment performance
  - Text similarity (TF-IDF cosine)
"""

import json
import logging

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── Ordered feature vector definition ────────────────────────────
FEATURE_NAMES = [
    # Skill features (0-8)
    'skill_match_ratio',
    'total_matched_skills',
    'total_required_skills',
    'missing_mandatory_count',
    'avg_matched_proficiency',
    'min_matched_proficiency',
    'avg_proficiency_gap',
    'max_proficiency_gap',
    'overconfidence_avg',
    # Experience features (9-11)
    'experience_delta',
    'experience_ratio',
    'meets_experience_req',
    # Education features (12-13)
    'education_level',
    'cgpa_normalized',
    # Profile richness (14-18)
    'num_projects',
    'num_certifications',
    'num_internships',
    'has_work_experience',
    'profile_completeness',
    # Assessment features (19-21)
    'assessment_pass_rate',
    'avg_assessment_score',
    'num_verified_skills',
    # Text similarity (22)
    'text_similarity',
]

N_FEATURES = len(FEATURE_NAMES)

# ── Degree → ordinal mapping ─────────────────────────────────────
_EDUCATION_LEVELS = {
    'high school': 1, 'diploma': 1.5, 'associate': 1.5,
    'bachelor': 2, 'bachelors': 2, "bachelor's": 2,
    'b.tech': 2, 'b.sc': 2, 'b.e': 2, 'bca': 2,
    'master': 3, 'masters': 3, "master's": 3,
    'm.tech': 3, 'm.sc': 3, 'mca': 3, 'mba': 3,
    'phd': 4, 'doctorate': 4, 'ph.d': 4,
}

# Fields checked for profile-completeness score
_PROFILE_FIELDS = [
    'technical_skills', 'objective', 'degree', 'university',
    'projects', 'certifications', 'work_experience',
]


# ── Helper utilities ──────────────────────────────────────────────

def _safe_json(value):
    """Parse a value that may be a JSON string, list, or None → list."""
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _get_job_skills(job):
    """Return lowercase skill names from Job.skills (handles both formats)."""
    raw = getattr(job, 'skills', None) or []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raw = [s.strip() for s in raw.split(',') if s.strip()]
    out = []
    for s in raw:
        name = s.get('name', '').strip().lower() if isinstance(s, dict) else str(s).strip().lower()
        if name:
            out.append(name)
    return out


def _get_user_skills(user):
    """Return lowercase skill names from User (CSV or list)."""
    if hasattr(user, 'get_all_skills_list'):
        return [s.lower() for s in user.get_all_skills_list() if s]
    ts = getattr(user, 'technical_skills', '') or ''
    ss = getattr(user, 'soft_skills', '') or ''
    return [s.strip().lower() for s in (ts + ',' + ss).split(',') if s.strip()]


def _encode_education(degree_str):
    if not degree_str:
        return 0
    d = degree_str.strip().lower()
    for keyword, level in _EDUCATION_LEVELS.items():
        if keyword in d:
            return level
    return 1  # fallback


def _build_text(obj, fields):
    """Concatenate non-empty string fields and JSON list fields."""
    parts = []
    for f in fields:
        val = getattr(obj, f, None)
        if val is None:
            continue
        if isinstance(val, str) and val.strip():
            parts.append(val)
        elif isinstance(val, (list, dict)):
            items = _safe_json(val) if isinstance(val, str) else (val if isinstance(val, list) else [val])
            for item in items:
                if isinstance(item, dict):
                    parts.extend(str(v) for v in item.values() if v)
                else:
                    parts.append(str(item))
    return ' '.join(parts)


def _text_similarity(text_a, text_b):
    """TF-IDF cosine similarity between two documents."""
    if not text_a.strip() or not text_b.strip():
        return 0.0
    try:
        tfidf = TfidfVectorizer(max_features=3000, stop_words='english')
        matrix = tfidf.fit_transform([text_a, text_b])
        return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except Exception:
        return 0.0


# ── Main extraction function ─────────────────────────────────────

def extract_features(user, job, user_skill_scores=None, assessment_attempts=None):
    """
    Extract the full feature vector for one (user, job) pair.

    Parameters
    ----------
    user : accounts.models.User
    job  : recruiter.models.Job
    user_skill_scores : list[assessments.models.UserSkillScore], optional
    assessment_attempts : list[assessments.models.AssessmentAttempt], optional

    Returns
    -------
    dict  –  {feature_name: float}
    """
    # ── Skill sets ────────────────────────────────────────────────
    user_skills = set(_get_user_skills(user))
    job_skills = _get_job_skills(job)
    job_skill_set = set(job_skills)
    matched = user_skills & job_skill_set
    n_required = len(job_skill_set) or 1

    skill_match_ratio = len(matched) / n_required

    # ── Proficiency features ──────────────────────────────────────
    matched_profs, prof_gaps, oc_values = [], [], []
    missing_mandatory = 0

    score_map = {}
    if user_skill_scores:
        for uss in user_skill_scores:
            sname = ''
            if hasattr(uss, 'skill') and uss.skill:
                sname = (uss.skill.name if hasattr(uss.skill, 'name') else str(uss.skill)).lower()
            score_map[sname] = uss

    req_map = {}
    if hasattr(job, 'skill_requirements'):
        try:
            for req in job.skill_requirements.all():
                rn = req.skill.name.lower() if req.skill else ''
                req_map[rn] = req
        except Exception:
            pass

    for skill_name in job_skill_set:
        uss = score_map.get(skill_name)
        req = req_map.get(skill_name)
        req_prof = req.required_proficiency if req else 5.0

        if uss and getattr(uss, 'status', '') == 'verified':
            v = uss.verified_level or 0
            sr = uss.self_rated_level or 0
            matched_profs.append(v)
            prof_gaps.append(max(req_prof - v, 0))
            oc_values.append(sr - v)
        elif skill_name in matched:
            matched_profs.append(3.0)
            prof_gaps.append(max(req_prof - 3.0, 0))
        else:
            if req and getattr(req, 'is_mandatory', False):
                missing_mandatory += 1

    avg_prof = float(np.mean(matched_profs)) if matched_profs else 0.0
    min_prof = float(min(matched_profs)) if matched_profs else 0.0
    avg_gap = float(np.mean(prof_gaps)) if prof_gaps else 0.0
    max_gap = float(max(prof_gaps)) if prof_gaps else 0.0
    oc_avg = float(np.mean(oc_values)) if oc_values else 0.0

    # ── Experience ────────────────────────────────────────────────
    u_exp = getattr(user, 'experience', 0) or 0
    j_exp = getattr(job, 'experience', 0) or 0
    exp_delta = u_exp - j_exp
    exp_ratio = min(u_exp / max(j_exp, 1), 5.0)

    # ── Education ─────────────────────────────────────────────────
    edu = _encode_education(getattr(user, 'degree', ''))
    cgpa = float(getattr(user, 'cgpa', 0) or 0) / 10.0

    # ── Profile richness ──────────────────────────────────────────
    projects = _safe_json(getattr(user, 'projects', None))
    certs = _safe_json(getattr(user, 'certifications', None))
    interns = _safe_json(getattr(user, 'internships', None))
    work = _safe_json(getattr(user, 'work_experience', None))
    filled = sum(1 for f in _PROFILE_FIELDS if getattr(user, f, None))
    completeness = filled / len(_PROFILE_FIELDS)

    # ── Assessment performance ────────────────────────────────────
    pass_rate, avg_score, n_verified = 0.0, 0.0, 0
    if assessment_attempts:
        done = [a for a in assessment_attempts if getattr(a, 'status', '') == 'completed']
        if done:
            pass_rate = sum(1 for a in done if getattr(a, 'passed', False)) / len(done)
            avg_score = float(np.mean([getattr(a, 'percentage', 0) or 0 for a in done])) / 100.0
    if user_skill_scores:
        n_verified = sum(1 for s in user_skill_scores if getattr(s, 'status', '') == 'verified')

    # ── Text similarity ───────────────────────────────────────────
    user_text = _build_text(user, ['objective', 'technical_skills', 'soft_skills',
                                    'job_title', 'industry', 'projects',
                                    'certifications', 'work_experience'])
    job_text = _build_text(job, ['title', 'description', 'requirements', 'company'])
    job_text += ' ' + ' '.join(_get_job_skills(job))
    text_sim = _text_similarity(user_text, job_text)

    return {
        'skill_match_ratio': skill_match_ratio,
        'total_matched_skills': len(matched),
        'total_required_skills': len(job_skill_set),
        'missing_mandatory_count': missing_mandatory,
        'avg_matched_proficiency': avg_prof,
        'min_matched_proficiency': min_prof,
        'avg_proficiency_gap': avg_gap,
        'max_proficiency_gap': max_gap,
        'overconfidence_avg': oc_avg,
        'experience_delta': exp_delta,
        'experience_ratio': exp_ratio,
        'meets_experience_req': 1 if u_exp >= j_exp else 0,
        'education_level': edu,
        'cgpa_normalized': cgpa,
        'num_projects': len(projects),
        'num_certifications': len(certs),
        'num_internships': len(interns),
        'has_work_experience': 1 if work else 0,
        'profile_completeness': completeness,
        'assessment_pass_rate': pass_rate,
        'avg_assessment_score': avg_score,
        'num_verified_skills': n_verified,
        'text_similarity': text_sim,
    }
