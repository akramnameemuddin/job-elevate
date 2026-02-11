"""
CareerGuidanceAgent  –  Student / Professional side
====================================================
ADK-style agent that analyses a user's profile, recommends jobs via the
existing ML engine, computes skill-gap summaries, and generates learning
roadmaps through the existing LearningPathGenerator.

Public entry-point
------------------
    agent = CareerGuidanceAgent()
    result = agent.get_career_recommendations(user_id, target_job_id=None)
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from django.db.models import Avg

from .adk_runtime import BaseAgent, tool

logger = logging.getLogger(__name__)


class CareerGuidanceAgent(BaseAgent):
    """
    Agent that serves students and professionals:
    1. Reads user profile + verified skills.
    2. Fetches recommended jobs via ML recommender.
    3. Computes a detailed skill-gap analysis for a target job.
    4. Generates a learning roadmap for top skill gaps.
    5. Produces human-readable next-step suggestions.
    """

    name = "CareerGuidanceAgent"
    description = (
        "Analyses user profiles, recommends matching jobs using ML, "
        "identifies skill gaps, and builds personalised learning roadmaps."
    )

    # ------------------------------------------------------------------
    # Tools (called by the LLM or directly from Python)
    # ------------------------------------------------------------------

    @tool
    def fetch_user_profile(self, user_id: int) -> dict:
        """Fetch user profile including technical skills, experience, and education."""
        from accounts.models import User

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return {"error": f"User {user_id} not found"}

        return {
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
            "projects": user.get_projects() if hasattr(user, "get_projects") else [],
            "certifications": user.get_certifications() if hasattr(user, "get_certifications") else [],
        }

    @tool
    def fetch_user_skills(self, user_id: int) -> list:
        """Fetch verified/claimed skill scores from UserSkillScore model."""
        from assessments.models import UserSkillScore

        scores = UserSkillScore.objects.filter(user_id=user_id).select_related("skill")
        return [
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

    @tool
    def fetch_assessment_attempts(self, user_id: int) -> list:
        """Fetch recent assessment attempts and scores."""
        from assessments.models import AssessmentAttempt

        attempts = (
            AssessmentAttempt.objects.filter(user_id=user_id, status="completed")
            .select_related("skill")
            .order_by("-started_at")[:20]
        )
        return [
            {
                "skill_name": a.skill.name if a.skill else "Unknown",
                "percentage": float(a.percentage),
                "proficiency_level": float(a.proficiency_level),
                "passed": a.passed,
                "completed_at": str(a.completed_at) if a.completed_at else None,
            }
            for a in attempts
        ]

    @tool
    def fetch_recommended_jobs(self, user_id: int) -> list:
        """Use ContentBasedRecommender to get ML-ranked job recommendations."""
        from accounts.models import User
        from jobs.recommendation_engine import ContentBasedRecommender

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return []

        recommender = ContentBasedRecommender()
        recs = recommender.recommend_jobs(user, limit=10)
        return [
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

    @tool
    def compute_skill_gap(self, user_id: int, job_id: int) -> dict:
        """Compare user skills against a target job's requirements and return gap analysis."""
        from accounts.models import User
        from assessments.models import UserSkillScore
        from recruiter.models import Job, JobSkillRequirement

        try:
            user = User.objects.get(pk=user_id)
            job = Job.objects.get(pk=job_id)
        except (User.DoesNotExist, Job.DoesNotExist) as exc:
            return {"error": str(exc)}

        # Gather user skill levels (verified preferred)
        user_scores = {
            s.skill.name.lower(): {
                "level": float(s.verified_level) if s.status == "verified" else float(s.self_rated_level),
                "status": s.status,
                "skill_id": s.skill.id,
            }
            for s in UserSkillScore.objects.filter(user=user).select_related("skill")
        }

        # Also include CSV technical_skills (level 0 assumed if no score exists)
        for sk in user.get_skills_list():
            key = sk.lower().strip()
            if key and key not in user_scores:
                user_scores[key] = {"level": 0.0, "status": "claimed", "skill_id": None}

        # Gather job requirements
        job_reqs: Dict[str, dict] = {}

        # From JobSkillRequirement (structured)
        for req in JobSkillRequirement.objects.filter(job=job).select_related("skill"):
            job_reqs[req.skill.name.lower()] = {
                "required_level": float(req.required_proficiency),
                "criticality": float(req.criticality),
                "skill_id": req.skill.id,
            }

        # From Job.skills JSON field (may be list of str or list of dict)
        for s in job.skills or []:
            name = s.get("name", s) if isinstance(s, dict) else s
            key = str(name).lower().strip()
            if key and key not in job_reqs:
                prof = float(s.get("proficiency", 5)) if isinstance(s, dict) else 5.0
                job_reqs[key] = {"required_level": prof, "criticality": 0.5, "skill_id": None}

        # Compute gaps
        critical_gaps: List[dict] = []
        development_areas: List[dict] = []
        strengths: List[dict] = []

        for skill_name, req in job_reqs.items():
            user_info = user_scores.get(skill_name, {"level": 0.0, "status": "missing"})
            gap = req["required_level"] - user_info["level"]
            entry = {
                "skill": skill_name,
                "user_level": user_info["level"],
                "required_level": req["required_level"],
                "gap": round(gap, 1),
                "status": user_info["status"],
            }
            if user_info["status"] == "missing" or gap > 3:
                critical_gaps.append(entry)
            elif gap > 0:
                development_areas.append(entry)
            else:
                strengths.append(entry)

        total_skills = len(job_reqs)
        matched = len(strengths)
        match_pct = round((matched / total_skills * 100), 1) if total_skills else 0.0

        return {
            "job_id": job.id,
            "job_title": job.title,
            "company": job.company,
            "total_required_skills": total_skills,
            "critical_gaps": sorted(critical_gaps, key=lambda x: x["gap"], reverse=True),
            "development_areas": sorted(development_areas, key=lambda x: x["gap"], reverse=True),
            "strengths": strengths,
            "match_percentage": match_pct,
        }

    @tool
    def generate_learning_roadmap(self, user_id: int, skill_gaps: list) -> list:
        """Generate learning paths for top skill gaps via LearningPathGenerator."""
        from accounts.models import User
        from assessments.models import Skill
        from learning.learning_path_generator import LearningPathGenerator

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return [{"error": f"User {user_id} not found"}]

        roadmap: list = []
        # Take top 3 gaps max to conserve API tokens
        for gap_info in skill_gaps[:3]:
            skill_name = gap_info.get("skill", "")
            current_level = gap_info.get("user_level", 0)
            required_level = gap_info.get("required_level", 6)

            skill_qs = Skill.objects.filter(name__iexact=skill_name)
            if not skill_qs.exists():
                roadmap.append({
                    "skill": skill_name,
                    "message": "Skill not found in assessment database – manual study recommended.",
                    "estimated_weeks": max(int((required_level - current_level) * 2), 2),
                })
                continue

            skill = skill_qs.first()
            try:
                path = LearningPathGenerator.generate_personalized_path(
                    user=user,
                    skill=skill,
                    current_level=current_level,
                    target_level=required_level,
                )
                roadmap.append({
                    "skill": skill_name,
                    "learning_path_id": path.id,
                    "title": path.title,
                    "description": path.description,
                    "estimated_weeks": path.estimated_weeks,
                    "estimated_hours": path.estimated_hours,
                    "status": path.status,
                })
            except Exception as exc:
                logger.warning("Learning path generation failed for %s: %s", skill_name, exc)
                roadmap.append({
                    "skill": skill_name,
                    "message": f"Generation failed – {exc}",
                    "estimated_weeks": max(int((required_level - current_level) * 2), 2),
                })

        return roadmap

    # ------------------------------------------------------------------
    # High-level public API (called by orchestrator)
    # ------------------------------------------------------------------

    def get_career_recommendations(
        self,
        user_id: int,
        target_job_id: Optional[int] = None,
    ) -> dict:
        """
        Full career-guidance pipeline:
        1. Fetch user profile + skills + attempts.
        2. Recommend jobs via ML.
        3. If *target_job_id* is given, compute gap & learning roadmap.
        4. Ask Gemini to synthesise human-readable next steps.
        5. Return combined JSON dict.
        """
        # Step 1 – gather data (tool calls executed directly)
        profile = self.fetch_user_profile(user_id=user_id)
        if "error" in profile:
            return profile

        skills = self.fetch_user_skills(user_id=user_id)
        attempts = self.fetch_assessment_attempts(user_id=user_id)
        recommended_jobs = self.fetch_recommended_jobs(user_id=user_id)

        # Step 2 – skill gap & learning path (optional)
        skill_analysis = {}
        learning_roadmap = []

        if target_job_id:
            skill_analysis = self.compute_skill_gap(user_id=user_id, job_id=target_job_id)
            if "error" not in skill_analysis:
                all_gaps = skill_analysis.get("critical_gaps", []) + skill_analysis.get("development_areas", [])
                if all_gaps:
                    learning_roadmap = self.generate_learning_roadmap(
                        user_id=user_id,
                        skill_gaps=all_gaps,
                    )
        elif recommended_jobs:
            # Auto-select top job for gap analysis
            top_job_id = recommended_jobs[0]["job_id"]
            skill_analysis = self.compute_skill_gap(user_id=user_id, job_id=top_job_id)
            if "error" not in skill_analysis:
                all_gaps = skill_analysis.get("critical_gaps", []) + skill_analysis.get("development_areas", [])
                if all_gaps:
                    learning_roadmap = self.generate_learning_roadmap(
                        user_id=user_id,
                        skill_gaps=all_gaps,
                    )

        # Step 3 – ask Gemini for synthesised next_steps
        next_steps = self._generate_next_steps(profile, skills, skill_analysis, learning_roadmap)

        # Step 4 - get user cluster info if available
        cluster_info = self._get_user_cluster_info(user_id)

        return {
            "user_profile": profile,
            "recommended_jobs": recommended_jobs,
            "skill_analysis": skill_analysis,
            "learning_roadmap": learning_roadmap,
            "next_steps": next_steps,
            "cluster_info": cluster_info,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_next_steps(
        self,
        profile: dict,
        skills: list,
        skill_analysis: dict,
        learning_roadmap: list,
    ) -> List[str]:
        """Use Gemini to produce 3-5 actionable next-step suggestions."""
        context = {
            "profile_summary": {
                "name": profile.get("full_name"),
                "skills": profile.get("technical_skills"),
                "experience": profile.get("experience_years"),
            },
            "verified_skills_count": sum(1 for s in skills if s.get("status") == "verified"),
            "critical_gaps": [g["skill"] for g in skill_analysis.get("critical_gaps", [])],
            "development_areas": [g["skill"] for g in skill_analysis.get("development_areas", [])],
            "match_percentage": skill_analysis.get("match_percentage", 0),
            "learning_paths": len(learning_roadmap),
        }

        message = (
            "Based on the context provided, generate 3-5 concrete, actionable "
            "next-step suggestions for this user to improve their career prospects. "
            "Return JSON: {\"next_steps\": [\"step1\", \"step2\", ...]}"
        )

        try:
            result = self.run(message, context=context)
            return result.get("next_steps", self._fallback_next_steps(skill_analysis))
        except Exception:
            return self._fallback_next_steps(skill_analysis)

    @staticmethod
    def _fallback_next_steps(skill_analysis: dict) -> List[str]:
        """Deterministic fallback when Gemini is unavailable."""
        steps = []
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

    @staticmethod
    def _get_user_cluster_info(user_id: int) -> dict:
        """Return user cluster label from the clustering module (if available)."""
        try:
            from jobs.clustering import get_user_cluster
            return get_user_cluster(user_id)
        except Exception:
            return {"cluster": "unknown", "label": "Not yet classified"}
