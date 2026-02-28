"""
Multi-Agent Orchestrator
========================
Defines the **root agent** that delegates to ``career_guidance_agent`` and
``recruiter_matching_agent`` using the official ``google-adk`` sub-agent
pattern, plus programmatic flow helpers that bypass the LLM for
deterministic demo pipelines.

Usage (LLM-driven delegation)
-----------------------------
    from agents.orchestrator import root_agent
    from agents.adk_runtime import create_runner, call_agent

    runner = create_runner(root_agent)
    reply = call_agent(runner, user_id="u1", session_id="s1",
                       query="Show me career recommendations")

Usage (deterministic flows)
---------------------------
    from agents.orchestrator import Orchestrator

    orch = Orchestrator()
    result = orch.run_career_flow(user, target_job_id=42)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.utils import timezone
from google.adk.agents import Agent

from .adk_runtime import MODEL_GEMINI
from .career_agent import career_agent, get_career_recommendations
from .recruiter_agent import recruiter_agent, rank_candidates_for_job
from .models import AgentMessage, AgentRunLog

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Root agent (official ADK multi-agent hierarchy)
# ──────────────────────────────────────────────────────────────────────

root_agent = Agent(
    name="job_elevate_orchestrator",
    model=MODEL_GEMINI,
    description=(
        "Top-level orchestrator for the JobElevate multi-agent system. "
        "Delegates career guidance queries to career_guidance_agent and "
        "recruiter / candidate-ranking queries to recruiter_matching_agent."
    ),
    instruction=(
        "You are the JobElevate Orchestrator.  Your role is to understand "
        "user requests and delegate them to the correct specialist agent.\n\n"
        "- For career advice, job recommendations, skill-gap analysis, or "
        "learning roadmaps → delegate to **career_guidance_agent**.\n"
        "- For candidate ranking, applicant scoring, or job-posting "
        "analytics → delegate to **recruiter_matching_agent**.\n\n"
        "Never answer domain questions yourself — always delegate.\n"
        "After receiving the specialist's response, present it clearly "
        "to the user."
    ),
    sub_agents=[career_agent, recruiter_agent],
)


# ──────────────────────────────────────────────────────────────────────
# Programmatic Orchestrator (deterministic flows for demo views)
# ──────────────────────────────────────────────────────────────────────

class Orchestrator:
    """
    Deterministic orchestration layer that calls agent tool functions
    directly (no LLM), logging every inter-agent message to the DB.
    """

    # ── DB helpers ────────────────────────────────────────────────

    @staticmethod
    def _log_message(
        sender: str,
        receiver: str,
        intent: str,
        payload: dict,
        run: Optional[AgentRunLog] = None,
    ) -> AgentMessage:
        msg = AgentMessage.objects.create(
            sender_agent=sender,
            receiver_agent=receiver,
            intent=intent,
            payload=payload,
        )
        if run:
            run.messages.add(msg)
        return msg

    @staticmethod
    def _start_run(user, run_type: str) -> AgentRunLog:
        return AgentRunLog.objects.create(user=user, run_type=run_type)

    @staticmethod
    def _finish_run(run: AgentRunLog, result: dict, status: str = "completed"):
        run.status = status
        run.result = result
        run.completed_at = timezone.now()
        run.save()

    # ── Career flow ───────────────────────────────────────────────

    def run_career_flow(
        self,
        user,
        target_job_id: Optional[int] = None,
    ) -> dict:
        """
        End-to-end career guidance pipeline.
        1. Orchestrator → CareerAgent: request analysis
        2. CareerAgent → Orchestrator: returns results
        """
        run = self._start_run(user, "career_flow")

        try:
            self._log_message(
                sender="orchestrator",
                receiver="career_guidance_agent",
                intent="career_analysis",
                payload={"user_id": user.id, "target_job_id": target_job_id},
                run=run,
            )

            result = get_career_recommendations(
                user_id=user.id,
                target_job_id=target_job_id,
            )

            self._log_message(
                sender="career_guidance_agent",
                receiver="orchestrator",
                intent="career_analysis_result",
                payload={"summary": _safe_summary(result)},
                run=run,
            )

            self._finish_run(run, result)

        except Exception as exc:
            logger.exception("Career flow failed: %s", exc)
            result = {"status": "error", "error_message": str(exc)}
            self._finish_run(run, result, status="failed")

        result["run_id"] = run.pk
        return result

    # ── Recruiter flow ────────────────────────────────────────────

    def run_recruiter_flow(self, user, job_id: int) -> dict:
        """
        Rank all applicants for *job_id*.
        1. Orchestrator → RecruiterAgent: rank candidates
        2. RecruiterAgent → Orchestrator: returns rankings
        """
        run = self._start_run(user, "recruiter_flow")

        try:
            self._log_message(
                sender="orchestrator",
                receiver="recruiter_matching_agent",
                intent="rank_candidates",
                payload={"job_id": job_id},
                run=run,
            )

            result = rank_candidates_for_job(job_id=job_id)

            self._log_message(
                sender="recruiter_matching_agent",
                receiver="orchestrator",
                intent="rank_candidates_result",
                payload={"summary": _safe_summary(result)},
                run=run,
            )

            self._finish_run(run, result)

        except Exception as exc:
            logger.exception("Recruiter flow failed: %s", exc)
            result = {"status": "error", "error_message": str(exc)}
            self._finish_run(run, result, status="failed")

        result["run_id"] = run.pk
        return result

    # ── Full multi-agent demo ─────────────────────────────────────

    def run_full_multi_agent_flow(
        self,
        user,
        job_id: int,
    ) -> dict:
        """
        Combined pipeline: career analysis → recruiter ranking.
        Demonstrates both agents co-operating under one orchestrator run.
        """
        run = self._start_run(user, "full_multi_agent")

        try:
            # Phase 1 — Career analysis
            self._log_message(
                sender="orchestrator",
                receiver="career_guidance_agent",
                intent="career_analysis",
                payload={"user_id": user.id, "target_job_id": job_id},
                run=run,
            )

            career_result = get_career_recommendations(
                user_id=user.id,
                target_job_id=job_id,
            )

            self._log_message(
                sender="career_guidance_agent",
                receiver="orchestrator",
                intent="career_analysis_result",
                payload={"summary": _safe_summary(career_result)},
                run=run,
            )

            # Phase 2 — Recruiter ranking
            self._log_message(
                sender="orchestrator",
                receiver="recruiter_matching_agent",
                intent="rank_candidates",
                payload={"job_id": job_id},
                run=run,
            )

            recruiter_result = rank_candidates_for_job(job_id=job_id)

            self._log_message(
                sender="recruiter_matching_agent",
                receiver="orchestrator",
                intent="rank_candidates_result",
                payload={"summary": _safe_summary(recruiter_result)},
                run=run,
            )

            combined = {
                "status": "success",
                "career": career_result,
                "recruiter": recruiter_result,
            }
            self._finish_run(run, combined)

        except Exception as exc:
            logger.exception("Full multi-agent flow failed: %s", exc)
            combined = {"status": "error", "error_message": str(exc)}
            self._finish_run(run, combined, status="failed")

        combined["run_id"] = run.pk
        return combined


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _safe_summary(result: dict) -> dict:
    """Return a compact payload safe for JSON storage (strip large lists)."""
    summary: Dict[str, Any] = {"status": result.get("status", "unknown")}

    if "match_percentage" in result:
        summary["match_percentage"] = result["match_percentage"]
    if "ranked_candidates" in result:
        summary["n_candidates"] = len(result["ranked_candidates"])
        top = result["ranked_candidates"][:3] if result["ranked_candidates"] else []
        summary["top_candidates"] = [
            {"name": c.get("full_name"), "score": c.get("composite_score")}
            for c in top
        ]
    if "recommended_jobs" in result:
        summary["n_recommended_jobs"] = len(result["recommended_jobs"])
    if "skill_analysis" in result:
        sa = result["skill_analysis"]
        summary["critical_gaps"] = len(sa.get("critical_gaps", []))
        summary["match_pct"] = sa.get("match_percentage")

    return summary
