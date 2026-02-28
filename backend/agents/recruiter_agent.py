"""
RecruiterMatchingAgent — Recruiter side
========================================
Uses the official ``google-adk`` Agent class.

Provides tools for fetching job details, listing applicants, and scoring
candidates with a 5-component weighted algorithm.  A programmatic
``rank_candidates_for_job()`` helper is also exposed for the Orchestrator.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from google.adk.agents import Agent

from .adk_runtime import MODEL_GEMINI

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Scoring weights (must sum to 1.0)
# ──────────────────────────────────────────────────────────────────────

SCORING_WEIGHTS: Dict[str, float] = {
    "skill_match": 0.30,
    "verified_ratio": 0.15,
    "avg_assessment_score": 0.20,
    "first_try_pass_rate": 0.10,
    "proficiency_fit": 0.25,
}


# ──────────────────────────────────────────────────────────────────────
# Tool functions
# ──────────────────────────────────────────────────────────────────────

def fetch_job_details(job_id: int) -> dict:
    """Fetch full details of a job posting including skill requirements.

    Args:
        job_id (int): The ID of the job posting.

    Returns:
        dict: Job details with required skills and proficiency levels.
    """
    from recruiter.models import Job, JobSkillRequirement

    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        return {"status": "error", "error_message": f"Job {job_id} not found"}

    reqs = JobSkillRequirement.objects.filter(job=job).select_related("skill")
    skill_reqs = [
        {
            "skill_name": r.skill.name,
            "skill_id": r.skill.id,
            "required_proficiency": float(r.required_proficiency),
            "criticality": float(r.criticality),
            "is_mandatory": r.is_mandatory,
            "skill_type": r.skill_type,
        }
        for r in reqs
    ]

    # Fall back to JSON skills if no JobSkillRequirement rows exist
    if not skill_reqs and job.skills:
        for s in job.skills:
            if isinstance(s, dict):
                skill_reqs.append({
                    "skill_name": s.get("name", str(s)),
                    "required_proficiency": float(s.get("proficiency", 5)),
                    "criticality": 0.5,
                    "is_mandatory": False,
                    "skill_type": "important",
                })
            elif isinstance(s, str) and s.strip():
                skill_reqs.append({
                    "skill_name": s,
                    "required_proficiency": 5.0,
                    "criticality": 0.5,
                    "is_mandatory": False,
                    "skill_type": "important",
                })

    return {
        "status": "success",
        "job_id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "job_type": job.job_type,
        "experience_required": job.experience,
        "skill_requirements": skill_reqs,
        "applicant_count": job.applicant_count,
    }


def fetch_applicants(job_id: int) -> dict:
    """Fetch all applicants for a job posting with their profiles.

    Args:
        job_id (int): The ID of the job posting.

    Returns:
        dict: List of applicant profiles with their skill data.
    """
    from recruiter.models import Application, Job

    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        return {"status": "error", "error_message": f"Job {job_id} not found"}

    apps = Application.objects.filter(job=job).select_related("applicant")
    applicants = []
    for app in apps:
        u = app.applicant
        applicants.append({
            "user_id": u.id,
            "full_name": u.full_name or u.username,
            "user_type": u.user_type,
            "technical_skills": u.get_skills_list(),
            "experience_years": u.experience,
            "application_status": app.status,
            "applied_at": str(app.applied_at),
        })

    return {
        "status": "success",
        "job_id": job.id,
        "job_title": job.title,
        "applicants": applicants,
    }


def compute_candidate_score(user_id: int, job_id: int) -> dict:
    """Score a candidate against a job using multi-component weighted algorithm.

    Components:
    - skill_match (0.30): Jaccard overlap of required vs user skills
    - verified_ratio (0.15): Fraction of matched skills that are verified
    - avg_assessment_score (0.20): Mean assessment percentage for relevant skills
    - first_try_pass_rate (0.10): Fraction of assessments passed on first attempt
    - proficiency_fit (0.25): Weighted avg of (user_level / required_level)

    Args:
        user_id (int): The ID of the candidate.
        job_id (int): The ID of the job posting.

    Returns:
        dict: Detailed breakdown of match scores and overall composite score.
    """
    from accounts.models import User
    from assessments.models import AssessmentAttempt, UserSkillScore
    from recruiter.models import Job, JobSkillRequirement

    try:
        user = User.objects.get(pk=user_id)
        job = Job.objects.get(pk=job_id)
    except (User.DoesNotExist, Job.DoesNotExist) as exc:
        return {"status": "error", "error_message": str(exc)}

    # ── Build job requirements map ────────────────────────────────
    job_reqs: Dict[str, dict] = {}
    for req in JobSkillRequirement.objects.filter(job=job).select_related("skill"):
        job_reqs[req.skill.name.lower()] = {
            "required": float(req.required_proficiency),
            "criticality": float(req.criticality),
            "mandatory": req.is_mandatory,
        }
    if not job_reqs and job.skills:
        for s in job.skills:
            if isinstance(s, dict):
                name = s.get("name", str(s)).lower().strip()
                prof = float(s.get("proficiency", 5))
            elif isinstance(s, str):
                name = s.lower().strip()
                prof = 5.0
            else:
                continue
            if name:
                job_reqs[name] = {"required": prof, "criticality": 0.5, "mandatory": False}

    if not job_reqs:
        return {"status": "error", "error_message": "Job has no skill requirements"}

    # ── Build user skills map ─────────────────────────────────────
    user_skills: Dict[str, dict] = {}
    for s in UserSkillScore.objects.filter(user=user).select_related("skill"):
        user_skills[s.skill.name.lower()] = {
            "level": float(s.verified_level) if s.status == "verified" else float(s.self_rated_level),
            "verified": s.status == "verified",
        }
    for sk in user.get_skills_list():
        key = sk.lower().strip()
        if key and key not in user_skills:
            user_skills[key] = {"level": 0.0, "verified": False}

    # ── Component 1: skill_match (Jaccard overlap) ────────────────
    required_set = set(job_reqs.keys())
    user_set = set(user_skills.keys())
    matched = required_set & user_set
    skill_match = len(matched) / len(required_set) if required_set else 0.0

    # ── Component 2: verified_ratio ───────────────────────────────
    verified_count = sum(1 for s in matched if user_skills.get(s, {}).get("verified", False))
    verified_ratio = verified_count / len(matched) if matched else 0.0

    # ── Component 3: avg_assessment_score ─────────────────────────
    attempts = AssessmentAttempt.objects.filter(
        user=user, status="completed"
    ).select_related("skill")
    relevant_scores: List[float] = []
    first_try_passes = 0
    first_try_total = 0
    skill_attempts: Dict[str, list] = {}

    for a in attempts:
        if not a.skill:
            continue
        sn = a.skill.name.lower()
        if sn in required_set:
            relevant_scores.append(float(a.percentage))
            skill_attempts.setdefault(sn, []).append(a)

    avg_assessment_score = (sum(relevant_scores) / len(relevant_scores) / 100.0) if relevant_scores else 0.0

    # ── Component 4: first_try_pass_rate ──────────────────────────
    for sn, att_list in skill_attempts.items():
        att_list.sort(key=lambda a: a.started_at)
        first_try_total += 1
        if att_list[0].passed:
            first_try_passes += 1
    first_try_pass_rate = first_try_passes / first_try_total if first_try_total else 0.0

    # ── Component 5: proficiency_fit ──────────────────────────────
    importance = _compute_skill_importance(job_reqs)
    proficiency_sum = 0.0
    importance_sum = 0.0
    for skill_name, req_info in job_reqs.items():
        imp = importance.get(skill_name, 1.0)
        user_level = user_skills.get(skill_name, {}).get("level", 0.0)
        req_level = req_info["required"]
        fit = min(user_level / req_level, 1.0) if req_level > 0 else 1.0
        proficiency_sum += fit * imp
        importance_sum += imp
    proficiency_fit = proficiency_sum / importance_sum if importance_sum else 0.0

    # ── Composite score ───────────────────────────────────────────
    components = {
        "skill_match": round(skill_match, 4),
        "verified_ratio": round(verified_ratio, 4),
        "avg_assessment_score": round(avg_assessment_score, 4),
        "first_try_pass_rate": round(first_try_pass_rate, 4),
        "proficiency_fit": round(proficiency_fit, 4),
    }
    composite = sum(
        components[k] * SCORING_WEIGHTS[k] for k in SCORING_WEIGHTS
    )
    composite = round(composite, 4)

    feedback = _generate_recruiter_feedback(components, composite, matched, required_set)

    return {
        "status": "success",
        "user_id": user.id,
        "full_name": user.full_name or user.username,
        "job_id": job.id,
        "job_title": job.title,
        "composite_score": composite,
        "components": components,
        "weights": SCORING_WEIGHTS,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(required_set - matched),
        "feedback": feedback,
    }


# ──────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────

def _compute_skill_importance(job_reqs: Dict[str, dict]) -> Dict[str, float]:
    """Normalise criticality values into relative importance weights."""
    total = sum(r["criticality"] for r in job_reqs.values()) or 1.0
    return {name: r["criticality"] / total for name, r in job_reqs.items()}


def _generate_recruiter_feedback(
    components: dict,
    composite: float,
    matched: set,
    required: set,
) -> str:
    """Human-readable one-paragraph feedback for the recruiter."""
    missing = required - matched
    parts: List[str] = []

    if composite >= 0.8:
        parts.append("Strong candidate. ")
    elif composite >= 0.5:
        parts.append("Moderate match. ")
    else:
        parts.append("Weak match. ")

    if components["skill_match"] >= 0.8:
        parts.append(f"Covers {len(matched)}/{len(required)} required skills. ")
    else:
        parts.append(f"Missing {len(missing)} of {len(required)} required skills ({', '.join(sorted(missing)[:3])}). ")

    if components["verified_ratio"] < 0.5:
        parts.append("Most matched skills are unverified — consider requesting assessments. ")

    if components["avg_assessment_score"] >= 0.7:
        parts.append("Assessment performance is strong. ")
    elif components["avg_assessment_score"] > 0:
        parts.append("Assessment scores are moderate. ")

    if components["proficiency_fit"] < 0.5:
        parts.append("Proficiency levels fall short of requirements.")

    return "".join(parts).strip()


# ──────────────────────────────────────────────────────────────────────
# Agent definition (official google-adk Agent)
# ──────────────────────────────────────────────────────────────────────

recruiter_agent = Agent(
    name="recruiter_matching_agent",
    model=MODEL_GEMINI,
    description=(
        "Scores and ranks job applicants using a multi-component weighted "
        "algorithm.  Use this agent when a recruiter needs candidate rankings "
        "or detailed applicant analysis for a specific job posting."
    ),
    instruction=(
        "You are a Recruiter Matching Agent for the JobElevate platform. "
        "Your job is to help recruiters evaluate and rank candidates.\n\n"
        "When a recruiter asks to rank candidates for a job:\n"
        "1. Use 'fetch_job_details' to understand the role and its skill requirements.\n"
        "2. Use 'fetch_applicants' to get the list of applicants.\n"
        "3. For each applicant, use 'compute_candidate_score' to get a detailed breakdown.\n"
        "4. Present candidates ranked by composite score, with key insights.\n\n"
        "Always explain why a candidate scored high or low by referencing "
        "specific scoring components (skill_match, verified_ratio, etc.)."
    ),
    tools=[
        fetch_job_details,
        fetch_applicants,
        compute_candidate_score,
    ],
)


# ──────────────────────────────────────────────────────────────────────
# Direct programmatic API (used by Orchestrator without LLM loop)
# ──────────────────────────────────────────────────────────────────────

def rank_candidates_for_job(job_id: int) -> dict:
    """
    Score every applicant and return them ranked by composite score.
    Fully deterministic — no LLM round-trips.
    """
    job_info = fetch_job_details(job_id=job_id)
    if job_info.get("status") == "error":
        return job_info

    applicants_data = fetch_applicants(job_id=job_id)
    if applicants_data.get("status") == "error":
        return applicants_data

    ranked: List[dict] = []
    for applicant in applicants_data.get("applicants", []):
        score_data = compute_candidate_score(
            user_id=applicant["user_id"],
            job_id=job_id,
        )
        if score_data.get("status") == "success":
            ranked.append(score_data)

    ranked.sort(key=lambda x: x["composite_score"], reverse=True)

    return {
        "status": "success",
        "job": job_info,
        "ranked_candidates": ranked,
        "total_applicants": len(applicants_data.get("applicants", [])),
        "scored_applicants": len(ranked),
    }
