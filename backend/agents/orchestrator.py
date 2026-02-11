"""
Multi-Agent Orchestrator
========================
Coordinates CareerGuidanceAgent and RecruiterMatchingAgent, passes
structured messages between them, and logs every exchange to the
AgentMessage model for demo transparency.

Flows
-----
1. ``run_career_flow(user_id, target_job_id)``
   – Uses CareerGuidanceAgent only; returns recommendations + gaps + roadmap.

2. ``run_recruiter_flow(job_id)``
   – Uses RecruiterMatchingAgent only; ranks applicants.

3. ``run_full_multi_agent_flow(user_id, job_id)``
   – End-to-end:
     a. CareerGuidanceAgent builds user summary for the job.
     b. Orchestrator sends "evaluate_candidates_for_job" to RecruiterMatchingAgent.
     c. RecruiterMatchingAgent ranks candidates and returns feedback.
     d. Orchestrator merges results and produces a combined response for
        students ("here's how recruiters think") and recruiters ("transparent ranking").
"""
from __future__ import annotations

import logging
from typing import Optional

from django.utils import timezone

from .career_agent import CareerGuidanceAgent
from .models import AgentMessage, AgentRunLog
from .recruiter_agent import RecruiterMatchingAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Stateful orchestrator that instantiates both agents, routes messages,
    and persists every interaction in the database.
    """

    def __init__(self):
        self.career_agent = CareerGuidanceAgent()
        self.recruiter_agent = RecruiterMatchingAgent()

    # ------------------------------------------------------------------
    # Message helpers
    # ------------------------------------------------------------------
    def _log_message(
        self,
        sender: str,
        receiver: str,
        intent: str,
        payload: dict,
        run_log: Optional[AgentRunLog] = None,
    ) -> AgentMessage:
        """Create an AgentMessage row and optionally attach to a run log."""
        msg = AgentMessage.objects.create(
            sender_agent=sender,
            receiver_agent=receiver,
            intent=intent,
            payload=payload,
        )
        if run_log:
            run_log.messages.add(msg)
        return msg

    def _start_run(self, run_type: str, user=None) -> AgentRunLog:
        return AgentRunLog.objects.create(
            user=user,
            run_type=run_type,
            status="running",
        )

    def _finish_run(self, run_log: AgentRunLog, result: dict, status: str = "completed"):
        run_log.status = status
        run_log.result = result
        run_log.completed_at = timezone.now()
        run_log.save()

    # ------------------------------------------------------------------
    # Flow 1: Career guidance only
    # ------------------------------------------------------------------
    def run_career_flow(
        self,
        user_id: int,
        target_job_id: Optional[int] = None,
    ) -> dict:
        """
        Student / professional flow:
        1. CareerGuidanceAgent analyses profile → jobs → gaps → learning roadmap.
        2. Every step is logged as an AgentMessage.
        """
        from accounts.models import User

        user = User.objects.filter(pk=user_id).first()
        run = self._start_run("career_flow", user=user)

        try:
            # Log the initial request
            self._log_message(
                sender="Orchestrator",
                receiver="CareerGuidanceAgent",
                intent="get_career_recommendations",
                payload={"user_id": user_id, "target_job_id": target_job_id},
                run_log=run,
            )

            result = self.career_agent.get_career_recommendations(
                user_id=user_id,
                target_job_id=target_job_id,
            )

            # Log the agent's response
            self._log_message(
                sender="CareerGuidanceAgent",
                receiver="Orchestrator",
                intent="career_recommendations_result",
                payload=_safe_payload(result),
                run_log=run,
            )

            self._finish_run(run, _safe_payload(result))
            return {"run_id": run.id, **result}

        except Exception as exc:
            logger.exception("Career flow failed")
            self._finish_run(run, {"error": str(exc)}, status="failed")
            return {"run_id": run.id, "error": str(exc)}

    # ------------------------------------------------------------------
    # Flow 2: Recruiter ranking only
    # ------------------------------------------------------------------
    def run_recruiter_flow(self, job_id: int) -> dict:
        """
        Recruiter flow:
        1. RecruiterMatchingAgent ranks candidates for the given job.
        2. Every step is logged.
        """
        from recruiter.models import Job

        job = Job.objects.filter(pk=job_id).first()
        user = job.posted_by if job else None
        run = self._start_run("recruiter_flow", user=user)

        try:
            self._log_message(
                sender="Orchestrator",
                receiver="RecruiterMatchingAgent",
                intent="rank_candidates_for_job",
                payload={"job_id": job_id},
                run_log=run,
            )

            result = self.recruiter_agent.rank_candidates_for_job(job_id=job_id)

            self._log_message(
                sender="RecruiterMatchingAgent",
                receiver="Orchestrator",
                intent="candidate_ranking_result",
                payload=_safe_payload(result),
                run_log=run,
            )

            self._finish_run(run, _safe_payload(result))
            return {"run_id": run.id, **result}

        except Exception as exc:
            logger.exception("Recruiter flow failed")
            self._finish_run(run, {"error": str(exc)}, status="failed")
            return {"run_id": run.id, "error": str(exc)}

    # ------------------------------------------------------------------
    # Flow 3: Full multi-agent communication
    # ------------------------------------------------------------------
    def run_full_multi_agent_flow(
        self,
        user_id: int,
        job_id: int,
    ) -> dict:
        """
        End-to-end multi-agent interaction:

        1. CareerGuidanceAgent → build user summary + skill gaps for the job.
        2. Orchestrator → sends "evaluate_candidates_for_job" to RecruiterMatchingAgent.
        3. RecruiterMatchingAgent → ranks candidates + returns feedback.
        4. Orchestrator → merges results, sends combined feedback to both sides.

        Returns a dict with keys for both student-facing and recruiter-facing views.
        """
        from accounts.models import User

        user = User.objects.filter(pk=user_id).first()
        run = self._start_run("full_multi_agent", user=user)

        try:
            # ---- Step 1: Career agent analyses user ----
            self._log_message(
                sender="Orchestrator",
                receiver="CareerGuidanceAgent",
                intent="analyse_user_for_job",
                payload={"user_id": user_id, "job_id": job_id},
                run_log=run,
            )

            career_result = self.career_agent.get_career_recommendations(
                user_id=user_id,
                target_job_id=job_id,
            )

            self._log_message(
                sender="CareerGuidanceAgent",
                receiver="Orchestrator",
                intent="user_analysis_complete",
                payload=_safe_payload(career_result),
                run_log=run,
            )

            # ---- Step 2: Send user profiles to recruiter agent ----
            self._log_message(
                sender="Orchestrator",
                receiver="RecruiterMatchingAgent",
                intent="evaluate_candidates_for_job",
                payload={
                    "job_id": job_id,
                    "requesting_user_id": user_id,
                    "career_summary": {
                        "match_percentage": career_result.get("skill_analysis", {}).get("match_percentage", 0),
                        "critical_gaps": [
                            g["skill"]
                            for g in career_result.get("skill_analysis", {}).get("critical_gaps", [])
                        ],
                    },
                },
                run_log=run,
            )

            recruiter_result = self.recruiter_agent.rank_candidates_for_job(job_id=job_id)

            self._log_message(
                sender="RecruiterMatchingAgent",
                receiver="Orchestrator",
                intent="candidate_ranking_complete",
                payload=_safe_payload(recruiter_result),
                run_log=run,
            )

            # ---- Step 3: Send recruiter feedback back to career agent context ----
            feedback = recruiter_result.get("feedback", {})
            if isinstance(feedback, str):
                # AI sometimes returns feedback as a plain string; wrap it in a dict
                feedback = {"summary": feedback}

            self._log_message(
                sender="RecruiterMatchingAgent",
                receiver="CareerGuidanceAgent",
                intent="recruiter_feedback",
                payload=_safe_payload(feedback),
                run_log=run,
            )

            # ---- Step 4: Merge and produce combined response ----
            # Find the requesting user in the ranking
            ranked_candidates = recruiter_result.get("ranked_candidates", [])
            user_rank = None
            user_fit_score = None
            total_applicants = len(ranked_candidates)

            for idx, c in enumerate(ranked_candidates, 1):
                if c.get("user_id") == user_id:
                    user_rank = idx
                    user_fit_score = c.get("fit_score", 0)
                    break

            # If the requesting user hasn't applied (not in ranked list),
            # compute their score separately so we can still show insights.
            if user_rank is None:
                try:
                    user_score_info = self.recruiter_agent.compute_candidate_score(
                        user_id=user_id,
                        job_id=job_id,
                    )
                    user_fit_score = user_score_info.get("score", 0)
                    # Insert them into the ranking to determine position
                    total_applicants = total_applicants + 1
                    user_rank = 1  # assume best until we find someone better
                    for c in ranked_candidates:
                        if c.get("fit_score", 0) >= user_fit_score:
                            user_rank += 1
                except Exception:
                    logger.debug("Could not compute score for requesting user %s", user_id)

            combined = {
                "run_id": run.id,
                # Student-facing
                "student_view": {
                    "recommended_jobs": career_result.get("recommended_jobs", []),
                    "skill_analysis": career_result.get("skill_analysis", {}),
                    "learning_roadmap": career_result.get("learning_roadmap", []),
                    "next_steps": career_result.get("next_steps", []),
                    "cluster_info": career_result.get("cluster_info", {}),
                    "recruiter_insights": {
                        "your_rank": user_rank,
                        "your_fit_score": user_fit_score,
                        "total_applicants": total_applicants,
                        "key_differentiators": feedback.get("key_differentiators", []),
                        "most_important_skills": feedback.get("most_important_skills", []),
                        "what_strong_candidates_have": feedback.get("typical_strong_candidate", {}),
                    },
                },
                # Recruiter-facing
                "recruiter_view": {
                    "job": recruiter_result.get("job", {}),
                    "ranked_candidates": recruiter_result.get("ranked_candidates", []),
                    "skill_importance": recruiter_result.get("skill_importance", []),
                    "feedback": feedback,
                },
            }

            self._log_message(
                sender="Orchestrator",
                receiver="Frontend",
                intent="combined_multi_agent_result",
                payload=_safe_payload(combined),
                run_log=run,
            )

            self._finish_run(run, _safe_payload(combined))
            return combined

        except Exception as exc:
            logger.exception("Full multi-agent flow failed")
            self._finish_run(run, {"error": str(exc)}, status="failed")
            return {"run_id": run.id, "error": str(exc)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_payload(data: dict) -> dict:
    """
    Ensure the payload is JSON-serialisable (strip Django model instances etc.).
    """
    import json

    try:
        json.dumps(data, default=str)
        return data
    except (TypeError, ValueError):
        return {"_serialisation_fallback": str(data)[:2000]}
