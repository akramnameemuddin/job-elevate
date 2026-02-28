"""
CareerGuidanceAgent — Student / Professional side
==================================================
Uses the official ``google-adk`` Agent class.

The agent is defined with plain-function tools that ADK automatically
wraps as ``FunctionTool``.  The LLM decides when to call them.

A direct ``get_career_recommendations()`` helper is also provided for
the Orchestrator to invoke programmatically (bypassing the LLM loop).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from google.adk.agents import Agent

from .adk_runtime import MODEL_GEMINI

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Tool functions (plain Python — ADK auto-discovers schema from
# signature + docstring)
# ──────────────────────────────────────────────────────────────────────

def fetch_user_profile(user_id: int) -> dict:
    """Fetch user profile including technical skills, experience, and education.

    Args:
        user_id (int): The ID of the user whose profile to fetch.

    Returns:
        dict: A dictionary with user profile data or an error message.
    """
    import django
    django.setup()
    from accounts.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {"status": "error", "error_message": f"User {user_id} not found"}

    return {
        "status": "success",
        "user_id": user.id,
        "full_name": user.full_name or user.username,
        "user_type": user.user_type,
        "technical_skills": user.get_skills_list(),
        "soft_skills": user.get_soft_skills_list(),
        "experience_years": user.experience,
        "job_title": user.job_title or "",
        "industry": user.industry or "",
        "university": user.university or "",
        "degree": user.degree or "",
        "objective": user.objective or "",
    }


def fetch_user_skills(user_id: int) -> dict:
    """Fetch verified and claimed skill scores from the assessment system.

    Args:
        user_id (int): The ID of the user.

    Returns:
        dict: A dictionary containing a list of skill scores with status.
    """
    from assessments.models import UserSkillScore

    scores = UserSkillScore.objects.filter(user_id=user_id).select_related("skill")
    skills_list = [
        {
            "skill_name": s.skill.name,
            "skill_id": s.skill.id,
            "verified_level": float(s.verified_level),
            "self_rated_level": float(s.self_rated_level),
            "status": s.status,
            "total_attempts": s.total_attempts,
            "best_score_pct": float(s.best_score_percentage),
        }
        for s in scores
    ]
    return {"status": "success", "skills": skills_list}


def fetch_assessment_attempts(user_id: int) -> dict:
    """Fetch recent completed assessment attempts and scores.

    Args:
        user_id (int): The ID of the user.

    Returns:
        dict: A dictionary with recent assessment attempt details.
    """
    from assessments.models import AssessmentAttempt

    attempts = (
        AssessmentAttempt.objects.filter(user_id=user_id, status="completed")
        .select_related("skill")
        .order_by("-started_at")[:20]
    )
    attempts_list = [
        {
            "skill_name": a.skill.name if a.skill else "Unknown",
            "percentage": float(a.percentage),
            "proficiency_level": float(a.proficiency_level),
            "passed": a.passed,
            "completed_at": str(a.completed_at) if a.completed_at else None,
        }
        for a in attempts
    ]
    return {"status": "success", "attempts": attempts_list}


def fetch_recommended_jobs(user_id: int) -> dict:
    """Use ML recommendation engine to get ranked job recommendations for the user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        dict: A dictionary with recommended jobs sorted by ML score.
    """
    from accounts.models import User
    from jobs.recommendation_engine import ContentBasedRecommender

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {"status": "error", "error_message": f"User {user_id} not found"}

    recommender = ContentBasedRecommender()
    recs = recommender.recommend_jobs(user, limit=10)
    jobs_list = [
        {
            "job_id": r["job"].id,
            "title": r["job"].title,
            "company": r["job"].company,
            "location": r["job"].location,
            "job_type": r["job"].job_type,
            "skills": r["job"].skills,
            "experience_required": r["job"].experience,
            "ml_score": round(float(r["score"]), 4),
            "reason": r["reason"],
        }
        for r in recs
    ]
    return {"status": "success", "recommended_jobs": jobs_list}


def compute_skill_gap(user_id: int, job_id: int) -> dict:
    """Compare user skills against a target job's requirements and return a gap analysis.

    Args:
        user_id (int): The ID of the user.
        job_id (int): The ID of the target job.

    Returns:
        dict: A dictionary with critical gaps, development areas, strengths, and match percentage.
    """
    from accounts.models import User
    from assessments.models import UserSkillScore
    from recruiter.models import Job, JobSkillRequirement

    try:
        user = User.objects.get(pk=user_id)
        job = Job.objects.get(pk=job_id)
    except (User.DoesNotExist, Job.DoesNotExist) as exc:
        return {"status": "error", "error_message": str(exc)}

    # Gather user skill levels
    user_scores: Dict[str, dict] = {}
    for s in UserSkillScore.objects.filter(user=user).select_related("skill"):
        user_scores[s.skill.name.lower()] = {
            "level": float(s.verified_level) if s.status == "verified" else float(s.self_rated_level),
            "status": s.status,
        }
    for sk in user.get_skills_list():
        key = sk.lower().strip()
        if key and key not in user_scores:
            user_scores[key] = {"level": 0.0, "status": "claimed"}

    # Gather job requirements
    job_reqs: Dict[str, float] = {}
    for req in JobSkillRequirement.objects.filter(job=job).select_related("skill"):
        job_reqs[req.skill.name.lower()] = float(req.required_proficiency)
    for s in job.skills or []:
        name = s.get("name", s) if isinstance(s, dict) else s
        key = str(name).lower().strip()
        if key and key not in job_reqs:
            job_reqs[key] = float(s.get("proficiency", 5)) if isinstance(s, dict) else 5.0

    # Compute gaps
    critical_gaps, development_areas, strengths = [], [], []
    for skill_name, req_level in job_reqs.items():
        user_info = user_scores.get(skill_name, {"level": 0.0, "status": "missing"})
        gap = req_level - user_info["level"]
        entry = {
            "skill": skill_name,
            "user_level": user_info["level"],
            "required_level": req_level,
            "gap": round(gap, 1),
            "status": user_info["status"],
        }
        if user_info["status"] == "missing" or gap > 3:
            critical_gaps.append(entry)
        elif gap > 0:
            development_areas.append(entry)
        else:
            strengths.append(entry)

    total = len(job_reqs)
    matched = len(strengths)
    match_pct = round((matched / total * 100), 1) if total else 0.0

    return {
        "status": "success",
        "job_title": job.title,
        "company": job.company,
        "total_required_skills": total,
        "critical_gaps": sorted(critical_gaps, key=lambda x: x["gap"], reverse=True),
        "development_areas": sorted(development_areas, key=lambda x: x["gap"], reverse=True),
        "strengths": strengths,
        "match_percentage": match_pct,
    }


def generate_learning_roadmap(user_id: int, skill_names: str) -> dict:
    """Generate learning paths for skill gaps using LearningPathGenerator.

    Args:
        user_id (int): The ID of the user.
        skill_names (str): Comma-separated list of skill names to generate paths for.

    Returns:
        dict: A dictionary with generated learning roadmap entries.
    """
    from accounts.models import User
    from assessments.models import Skill
    from learning.learning_path_generator import LearningPathGenerator

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {"status": "error", "error_message": f"User {user_id} not found"}

    roadmap = []
    for skill_name in skill_names.split(",")[:3]:
        skill_name = skill_name.strip()
        if not skill_name:
            continue
        skill_qs = Skill.objects.filter(name__iexact=skill_name)
        if not skill_qs.exists():
            roadmap.append({
                "skill": skill_name,
                "message": "Skill not in assessment DB — manual study recommended.",
            })
            continue
        skill = skill_qs.first()
        try:
            path = LearningPathGenerator.generate_personalized_path(
                user=user, skill=skill, current_level=0, target_level=6,
            )
            roadmap.append({
                "skill": skill_name,
                "learning_path_id": path.id,
                "title": path.title,
                "estimated_weeks": path.estimated_weeks,
            })
        except Exception as exc:
            logger.warning("Learning path generation failed for %s: %s", skill_name, exc)
            roadmap.append({"skill": skill_name, "message": f"Generation failed: {exc}"})

    return {"status": "success", "roadmap": roadmap}


# ──────────────────────────────────────────────────────────────────────
# Agent definition (official google-adk Agent)
# ──────────────────────────────────────────────────────────────────────

career_agent = Agent(
    name="career_guidance_agent",
    model=MODEL_GEMINI,
    description=(
        "Analyses user profiles, recommends matching jobs using ML, "
        "identifies skill gaps, and builds personalised learning roadmaps. "
        "Use this agent when a student or professional needs career advice."
    ),
    instruction=(
        "You are a Career Guidance Agent for the JobElevate platform. "
        "Your job is to help students and professionals with career advice.\n\n"
        "When a user asks for career recommendations:\n"
        "1. Use 'fetch_user_profile' to get their profile.\n"
        "2. Use 'fetch_user_skills' to see their verified skills.\n"
        "3. Use 'fetch_recommended_jobs' to get ML-ranked job matches.\n"
        "4. If a specific job is mentioned, use 'compute_skill_gap' to analyse gaps.\n"
        "5. For critical skill gaps, use 'generate_learning_roadmap' to create a study plan.\n\n"
        "Present results clearly and concisely with actionable next steps. "
        "Always be encouraging and suggest concrete improvements."
    ),
    tools=[
        fetch_user_profile,
        fetch_user_skills,
        fetch_assessment_attempts,
        fetch_recommended_jobs,
        compute_skill_gap,
        generate_learning_roadmap,
    ],
)


# ──────────────────────────────────────────────────────────────────────
# Direct programmatic API (used by Orchestrator without LLM loop)
# ──────────────────────────────────────────────────────────────────────

def get_career_recommendations(
    user_id: int,
    target_job_id: Optional[int] = None,
) -> dict:
    """
    Full career-guidance pipeline executed programmatically
    (tools called directly, no LLM round-trips).

    Returns a dict with: user_profile, recommended_jobs, skill_analysis,
    learning_roadmap, next_steps.
    """
    profile = fetch_user_profile(user_id=user_id)
    if profile.get("status") == "error":
        return profile

    skills = fetch_user_skills(user_id=user_id)
    attempts = fetch_assessment_attempts(user_id=user_id)
    recommended = fetch_recommended_jobs(user_id=user_id)

    skill_analysis: dict = {}
    learning_roadmap: list = []

    job_id = target_job_id
    if not job_id and recommended.get("recommended_jobs"):
        job_id = recommended["recommended_jobs"][0]["job_id"]

    if job_id:
        skill_analysis = compute_skill_gap(user_id=user_id, job_id=job_id)
        if skill_analysis.get("status") == "success":
            all_gaps = (
                skill_analysis.get("critical_gaps", [])
                + skill_analysis.get("development_areas", [])
            )
            if all_gaps:
                gap_names = ",".join(g["skill"] for g in all_gaps[:3])
                lr = generate_learning_roadmap(user_id=user_id, skill_names=gap_names)
                learning_roadmap = lr.get("roadmap", [])

    next_steps = _fallback_next_steps(skill_analysis)

    return {
        "user_profile": profile,
        "recommended_jobs": recommended.get("recommended_jobs", []),
        "skill_analysis": skill_analysis,
        "learning_roadmap": learning_roadmap,
        "next_steps": next_steps,
    }


def _fallback_next_steps(skill_analysis: dict) -> List[str]:
    """Deterministic next-step suggestions (no LLM needed)."""
    steps: List[str] = []
    critical = skill_analysis.get("critical_gaps", [])
    dev_areas = skill_analysis.get("development_areas", [])
    if critical:
        top = critical[0]["skill"]
        steps.append(f"Take the assessment for '{top}' to verify your skill level.")
        steps.append(f"Start a learning path to bridge the critical gap in '{top}'.")
    if dev_areas:
        steps.append(f"Improve your proficiency in '{dev_areas[0]['skill']}' to match the job requirement.")
    steps.append("Update your profile with recent projects and certifications.")
    steps.append("Apply to jobs that match your current skill set while upskilling.")
    return steps[:5]
