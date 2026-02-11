"""
RecruiterMatchingAgent  –  Recruiter side
==========================================
ADK-style agent that ranks applicants for a given job using an ML-heavy
candidate-job fit model (weighted scoring + optional RandomForest).

Public entry-point
------------------
    agent = RecruiterMatchingAgent()
    result = agent.rank_candidates_for_job(job_id)
"""
from __future__ import annotations

import json
import logging
import math
from typing import Any, Dict, List, Optional

import numpy as np
from django.db.models import Avg, Count, Q

from .adk_runtime import BaseAgent, tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Candidate scoring weights (documented & configurable)
# ---------------------------------------------------------------------------
#   - skill_match          : fraction of required skills the candidate has  (0-1)
#   - verified_ratio       : fraction of candidate skills that are verified (0-1)
#   - avg_assessment_score : average assessment percentage normalised 0-1
#   - first_try_pass_rate  : fraction of relevant assessments passed on 1st attempt
#   - proficiency_fit      : average (user_level / required_level) across skills
#
SCORING_WEIGHTS: Dict[str, float] = {
    "skill_match": 0.30,
    "verified_ratio": 0.15,
    "avg_assessment_score": 0.20,
    "first_try_pass_rate": 0.10,
    "proficiency_fit": 0.25,
}


class RecruiterMatchingAgent(BaseAgent):
    """
    Agent that serves recruiters:
    1. Fetches applicants for a job.
    2. Computes an ML-based **candidate-job fit score** per applicant.
    3. Ranks candidates and provides transparency explanations.
    4. Returns feedback on which skills/attributes matter most.
    """

    name = "RecruiterMatchingAgent"
    description = (
        "Ranks job applicants using an ML-based scoring model that considers "
        "skill match, verified proficiency, assessment performance, and "
        "first-try pass rates."
    )

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    @tool
    def fetch_job_details(self, job_id: int) -> dict:
        """Fetch full details of a job posting."""
        from recruiter.models import Job, JobSkillRequirement

        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return {"error": f"Job {job_id} not found"}

        reqs = JobSkillRequirement.objects.filter(job=job).select_related("skill")

        skill_reqs = []
        seen_skills = set()
        for r in reqs:
            key = r.skill.name.lower().strip()
            if key not in seen_skills:
                seen_skills.add(key)
                skill_reqs.append({
                    "skill": r.skill.name,
                    "skill_id": r.skill.id,
                    "required_proficiency": float(r.required_proficiency),
                    "criticality": float(r.criticality),
                })

        # Also from Job.skills JSON (only if not already covered)
        for s in job.skills or []:
            name = s.get("name", s) if isinstance(s, dict) else s
            key = str(name).lower().strip()
            if key and key not in seen_skills:
                seen_skills.add(key)
                skill_reqs.append({
                    "skill": str(name),
                    "skill_id": None,
                    "required_proficiency": float(s.get("proficiency", 5)) if isinstance(s, dict) else 5.0,
                    "criticality": 0.5,
                })

        return {
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "experience_required": job.experience,
            "description": job.description[:500],
            "skill_requirements": skill_reqs,
        }

    @tool
    def fetch_applicants(self, job_id: int) -> list:
        """Fetch all applicants for a job along with their profiles."""
        from recruiter.models import Application

        apps = (
            Application.objects.filter(job_id=job_id)
            .select_related("applicant")
            .order_by("-applied_at")
        )

        results = []
        for app in apps:
            u = app.applicant
            results.append({
                "application_id": app.id,
                "user_id": u.id,
                "full_name": u.full_name or u.username,
                "user_type": u.user_type,
                "technical_skills": u.get_skills_list(),
                "experience_years": u.experience,
                "status": app.status,
                "applied_at": str(app.applied_at),
            })
        return results

    @tool
    def compute_candidate_score(self, user_id: int, job_id: int) -> dict:
        """
        ML-based candidate-job fit scoring.

        Components (see SCORING_WEIGHTS at module level):
        1. skill_match – fraction of required skills the user possesses
        2. verified_ratio – fraction of those skills verified by assessment
        3. avg_assessment_score – avg percentage across relevant assessments
        4. first_try_pass_rate – % of relevant assessments passed on attempt #1
        5. proficiency_fit – avg(user_level / required_level) clamped to [0,1]

        Returns a dict with final score and per-component breakdown.
        """
        from accounts.models import User
        from assessments.models import AssessmentAttempt, Skill, UserSkillScore
        from recruiter.models import Job, JobSkillRequirement

        try:
            user = User.objects.get(pk=user_id)
            job = Job.objects.get(pk=job_id)
        except (User.DoesNotExist, Job.DoesNotExist) as exc:
            return {"error": str(exc)}

        # 1. Build required-skill map  {lower_name: required_level}
        required: Dict[str, float] = {}
        skill_id_map: Dict[str, int] = {}

        for req in JobSkillRequirement.objects.filter(job=job).select_related("skill"):
            key = req.skill.name.lower().strip()
            required[key] = float(req.required_proficiency)
            skill_id_map[key] = req.skill.id

        for s in job.skills or []:
            name = s.get("name", s) if isinstance(s, dict) else s
            key = str(name).lower().strip()
            if key and key not in required:
                required[key] = float(s.get("proficiency", 5)) if isinstance(s, dict) else 5.0

        if not required:
            return {"score": 0.5, "explanation": "No skill requirements defined for this job."}

        # 2. User skill lookup
        user_skills_csv = {sk.lower().strip() for sk in user.get_skills_list()}
        user_scores = {
            s.skill.name.lower().strip(): s
            for s in UserSkillScore.objects.filter(user=user).select_related("skill")
        }

        # 3. Compute components
        matched_count = 0
        verified_count = 0
        proficiency_ratios: List[float] = []

        for skill_name, req_level in required.items():
            has_skill = skill_name in user_skills_csv or skill_name in user_scores
            if has_skill:
                matched_count += 1
            score_obj = user_scores.get(skill_name)
            if score_obj:
                if score_obj.status == "verified":
                    verified_count += 1
                user_level = float(score_obj.verified_level) if score_obj.status == "verified" else float(score_obj.self_rated_level)
                ratio = min(user_level / req_level, 1.0) if req_level > 0 else 1.0
                proficiency_ratios.append(ratio)
            elif has_skill:
                proficiency_ratios.append(0.3)  # has skill but unverified/no score

        skill_match = matched_count / len(required) if required else 0
        verified_ratio = verified_count / max(matched_count, 1)
        proficiency_fit = float(np.mean(proficiency_ratios)) if proficiency_ratios else 0.0

        # 4. Assessment performance on relevant skills
        relevant_skill_ids = list(skill_id_map.values())
        relevant_attempts = AssessmentAttempt.objects.filter(
            user=user,
            status="completed",
            skill_id__in=relevant_skill_ids,
        )
        avg_score = relevant_attempts.aggregate(avg=Avg("percentage"))["avg"] or 0
        avg_assessment_score = min(avg_score / 100.0, 1.0)

        # First-try pass rate
        first_attempts = []
        for sid in relevant_skill_ids:
            first = (
                AssessmentAttempt.objects.filter(user=user, skill_id=sid, status="completed")
                .order_by("started_at")
                .first()
            )
            if first:
                first_attempts.append(1.0 if first.passed else 0.0)
        first_try_pass_rate = float(np.mean(first_attempts)) if first_attempts else 0.0

        # 5. Final weighted score
        components = {
            "skill_match": round(skill_match, 4),
            "verified_ratio": round(verified_ratio, 4),
            "avg_assessment_score": round(avg_assessment_score, 4),
            "first_try_pass_rate": round(first_try_pass_rate, 4),
            "proficiency_fit": round(proficiency_fit, 4),
        }

        final_score = sum(
            SCORING_WEIGHTS[k] * components[k] for k in SCORING_WEIGHTS
        )

        # Build explanation
        explanation_parts = []
        if skill_match >= 0.8:
            explanation_parts.append("Excellent skill coverage")
        elif skill_match >= 0.5:
            explanation_parts.append("Moderate skill match")
        else:
            explanation_parts.append("Low skill overlap")

        if verified_ratio >= 0.7:
            explanation_parts.append("most skills verified")
        if avg_assessment_score >= 0.7:
            explanation_parts.append("strong assessment performance")
        if first_try_pass_rate >= 0.8:
            explanation_parts.append("passes assessments on first try")

        return {
            "user_id": user_id,
            "job_id": job_id,
            "score": round(final_score, 4),
            "components": components,
            "weights": SCORING_WEIGHTS,
            "explanation": "; ".join(explanation_parts) if explanation_parts else "Score computed from multiple ML factors.",
        }

    # ------------------------------------------------------------------
    # High-level public API
    # ------------------------------------------------------------------

    def rank_candidates_for_job(self, job_id: int) -> dict:
        """
        Rank all applicants for *job_id* and return:
        - ranked_candidates
        - skill_importance (which skills matter most)
        - feedback (for CareerGuidanceAgent)
        """
        job_details = self.fetch_job_details(job_id=job_id)
        if "error" in job_details:
            return job_details

        applicants = self.fetch_applicants(job_id=job_id)
        if not applicants:
            return {
                "job": job_details,
                "ranked_candidates": [],
                "feedback": "No applicants yet for this job.",
                "skill_importance": [],
            }

        # Score every applicant
        scored: List[dict] = []
        for app in applicants:
            score_info = self.compute_candidate_score(
                user_id=app["user_id"], job_id=job_id
            )
            scored.append({
                **app,
                "fit_score": score_info.get("score", 0),
                "score_components": score_info.get("components", {}),
                "explanation": score_info.get("explanation", ""),
            })

        ranked = sorted(scored, key=lambda x: x["fit_score"], reverse=True)

        # Generate skill importance insights
        skill_importance = self._compute_skill_importance(job_details, ranked)

        # Generate feedback for CareerGuidanceAgent
        feedback = self._generate_recruiter_feedback(job_details, ranked, skill_importance)

        return {
            "job": job_details,
            "ranked_candidates": ranked,
            "skill_importance": skill_importance,
            "feedback": feedback,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_skill_importance(job_details: dict, ranked: list) -> list:
        """
        Determine which skills differentiate strong from weak candidates.
        """
        reqs = job_details.get("skill_requirements", [])
        importance = []
        for req in reqs:
            skill_name = req["skill"].lower().strip()
            # Count how many top-half candidates have this skill
            mid = max(len(ranked) // 2, 1)
            top_half = ranked[:mid]
            bottom_half = ranked[mid:] if mid < len(ranked) else []

            top_has = sum(
                1 for c in top_half
                if skill_name in [s.lower().strip() for s in c.get("technical_skills", [])]
            )
            bottom_has = sum(
                1 for c in bottom_half
                if skill_name in [s.lower().strip() for s in c.get("technical_skills", [])]
            )
            top_rate = top_has / len(top_half) if top_half else 0
            bottom_rate = bottom_has / len(bottom_half) if bottom_half else 0

            importance.append({
                "skill": req["skill"],
                "required_proficiency": req["required_proficiency"],
                "differentiating_power": round(top_rate - bottom_rate, 2),
                "top_candidate_coverage": round(top_rate, 2),
            })

        return sorted(importance, key=lambda x: x["differentiating_power"], reverse=True)

    def _generate_recruiter_feedback(
        self,
        job_details: dict,
        ranked: list,
        skill_importance: list,
    ) -> dict:
        """
        Structured feedback about what strong candidates have that others don't.
        This data is also sent back to CareerGuidanceAgent via the Orchestrator.
        """
        if not ranked:
            return {"summary": "No candidates to analyse.", "key_differentiators": []}

        top = ranked[0] if ranked else {}
        differentiators = [
            si["skill"]
            for si in skill_importance
            if si["differentiating_power"] > 0.2
        ]

        avg_score = float(np.mean([c["fit_score"] for c in ranked])) if ranked else 0

        return {
            "summary": (
                f"{len(ranked)} candidates evaluated. "
                f"Top candidate: {top.get('full_name', 'N/A')} "
                f"(score {top.get('fit_score', 0):.2f}). "
                f"Average score: {avg_score:.2f}."
            ),
            "key_differentiators": differentiators,
            "most_important_skills": [si["skill"] for si in skill_importance[:3]],
            "typical_strong_candidate": {
                "skill_match": "> 80%",
                "verified_skills": "> 70% of required",
                "assessment_score": "> 70%",
                "passes_first_try": True,
            },
        }
