"""
Agent Views
===========
Django views that expose the ADK-powered career and recruiter agents
to end-users via HTML pages (GET) and JSON API (POST).
"""
from __future__ import annotations

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import AgentMessage, AgentRunLog
from .orchestrator import Orchestrator

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Career Guidance (students / professionals)
# ──────────────────────────────────────────────────────────────────────

@login_required
def career_guidance_view(request):
    """GET  → render career_guidance.html with job list.
       POST → run career flow and return JSON."""
    from recruiter.models import Job

    available_jobs = Job.objects.filter(status="Open").order_by("-created_at")[:50]
    recent_runs = (
        AgentRunLog.objects.filter(user=request.user, run_type="career_flow")
        .order_by("-started_at")[:5]
    )

    if request.method == "POST":
        job_id = request.POST.get("job_id")
        target_job_id = int(job_id) if job_id else None

        try:
            orch = Orchestrator()
            result = orch.run_career_flow(request.user, target_job_id=target_job_id)
        except Exception as exc:
            logger.exception("Career guidance view error: %s", exc)
            return JsonResponse({"error": str(exc)}, status=500)

        if result.get("status") == "error":
            return JsonResponse({"error": result.get("error_message", "Unknown error")}, status=400)

        return JsonResponse(result)

    target_job = None
    job_id = request.GET.get("job_id")
    if job_id:
        try:
            target_job = Job.objects.get(pk=int(job_id))
        except (Job.DoesNotExist, ValueError):
            pass

    return render(request, "agents/career_guidance.html", {
        "available_jobs": available_jobs,
        "target_job": target_job,
        "recent_runs": recent_runs,
    })


# ──────────────────────────────────────────────────────────────────────
# Recruiter Agent
# ──────────────────────────────────────────────────────────────────────

@login_required
def recruiter_agent_view(request):
    """GET  → render recruiter_agent.html with recruiter's jobs.
       POST → run recruiter flow and return JSON."""
    from recruiter.models import Job

    my_jobs = Job.objects.filter(posted_by=request.user).order_by("-created_at")
    recent_runs = (
        AgentRunLog.objects.filter(user=request.user, run_type="recruiter_flow")
        .order_by("-started_at")[:5]
    )

    if request.method == "POST":
        job_id = request.POST.get("job_id")
        if not job_id:
            return JsonResponse({"error": "No job selected"}, status=400)

        try:
            orch = Orchestrator()
            result = orch.run_recruiter_flow(request.user, job_id=int(job_id))
        except Exception as exc:
            logger.exception("Recruiter view error: %s", exc)
            return JsonResponse({"error": str(exc)}, status=500)

        if result.get("status") == "error":
            return JsonResponse({"error": result.get("error_message", "Unknown error")}, status=400)

        # Transform data to match template expectations
        return JsonResponse(_transform_recruiter_response(result))

    selected_job = None
    job_id = request.GET.get("job_id")
    if job_id:
        try:
            selected_job = Job.objects.get(pk=int(job_id), posted_by=request.user)
        except (Job.DoesNotExist, ValueError):
            pass

    return render(request, "agents/recruiter_agent.html", {
        "my_jobs": my_jobs,
        "job": selected_job,
        "recent_runs": recent_runs,
    })


# ──────────────────────────────────────────────────────────────────────
# Multi-Agent Demo
# ──────────────────────────────────────────────────────────────────────

@login_required
def multi_agent_demo_view(request):
    """GET  → render multi_agent_demo.html.
       POST → run full multi-agent flow and return JSON."""
    from recruiter.models import Job

    jobs = Job.objects.filter(status="Open").order_by("-created_at")[:50]

    latest_run = (
        AgentRunLog.objects.filter(user=request.user, run_type="full_multi_agent")
        .order_by("-started_at")
        .first()
    )
    messages = latest_run.messages.order_by("created_at") if latest_run else []

    if request.method == "POST":
        job_id = request.POST.get("job_id")
        if not job_id:
            return JsonResponse({"error": "No job selected"}, status=400)

        try:
            orch = Orchestrator()
            result = orch.run_full_multi_agent_flow(request.user, job_id=int(job_id))
        except Exception as exc:
            logger.exception("Multi-agent demo error: %s", exc)
            return JsonResponse({"error": str(exc)}, status=500)

        if result.get("status") == "error":
            return JsonResponse({"error": result.get("error_message", "Unknown error")}, status=400)

        return JsonResponse(_transform_demo_response(result, request.user))

    return render(request, "agents/multi_agent_demo.html", {
        "jobs": jobs,
        "messages": messages,
        "latest_run": latest_run,
    })


# ──────────────────────────────────────────────────────────────────────
# Run Detail (JSON API for AJAX timeline fetch)
# ──────────────────────────────────────────────────────────────────────

@login_required
def agent_run_detail_view(request, run_id):
    """Return JSON with run details and messages."""
    run = get_object_or_404(AgentRunLog, pk=run_id)

    msgs = run.messages.order_by("created_at")
    return JsonResponse({
        "run_id": run.pk,
        "run_type": run.run_type,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "messages": [
            {
                "sender_agent": m.sender_agent,
                "receiver_agent": m.receiver_agent,
                "intent": m.intent,
                "created_at": m.created_at.isoformat(),
            }
            for m in msgs
        ],
    })


# ──────────────────────────────────────────────────────────────────────
# Response transformers  (backend dict → template-expected keys)
# ──────────────────────────────────────────────────────────────────────

def _transform_recruiter_response(result: dict) -> dict:
    """Map Orchestrator output to the keys the recruiter template JS expects."""
    raw_candidates = result.get("ranked_candidates", [])
    ranked = []
    for c in raw_candidates:
        ranked.append({
            "full_name": c.get("full_name", "Unknown"),
            "user_type": c.get("user_type", ""),
            "fit_score": c.get("composite_score", 0),
            "score_components": c.get("components", {}),
            "explanation": c.get("feedback", ""),
            "matched_skills": c.get("matched_skills", []),
            "missing_skills": c.get("missing_skills", []),
        })

    # Build skill importance data from job requirements
    job_info = result.get("job", {})
    skill_importance = []
    for sr in job_info.get("skill_requirements", []):
        skill_importance.append({
            "skill": sr.get("skill_name", ""),
            "required_proficiency": sr.get("required_proficiency", 5),
            "differentiating_power": sr.get("criticality", 0.5),
        })

    # Aggregate feedback
    summary_parts = []
    if ranked:
        top = ranked[0]
        summary_parts.append(
            f"Top candidate: {top['full_name']} "
            f"({(top['fit_score'] * 100):.0f}% fit). "
        )
    summary_parts.append(
        f"{len(ranked)} of {result.get('total_applicants', 0)} applicants scored."
    )

    return {
        "ranked_candidates": ranked,
        "skill_importance": skill_importance,
        "feedback": {
            "summary": " ".join(summary_parts),
            "key_differentiators": [
                s["skill"]
                for s in sorted(
                    skill_importance, key=lambda x: x["differentiating_power"], reverse=True
                )[:3]
            ],
            "most_important_skills": [
                s["skill"]
                for s in sorted(
                    skill_importance, key=lambda x: x["required_proficiency"], reverse=True
                )[:3]
            ],
        },
        "run_id": result.get("run_id"),
    }


def _transform_demo_response(result: dict, user) -> dict:
    """Map combined flow output to the multi_agent_demo template JS keys."""
    career = result.get("career", {})
    recruiter = result.get("recruiter", {})

    # Student view
    student_view = {
        "recommended_jobs": career.get("recommended_jobs", []),
        "skill_analysis": career.get("skill_analysis", {}),
        "learning_roadmap": career.get("learning_roadmap", []),
        "next_steps": career.get("next_steps", []),
        "recruiter_insights": _build_recruiter_insights(recruiter, user),
    }

    # Recruiter view
    raw_candidates = recruiter.get("ranked_candidates", [])
    ranked = []
    for c in raw_candidates:
        ranked.append({
            "full_name": c.get("full_name", "Unknown"),
            "fit_score": c.get("composite_score", 0),
            "explanation": c.get("feedback", ""),
        })

    recruiter_view = {
        "ranked_candidates": ranked,
        "feedback": {
            "summary": (
                f"{len(ranked)} candidates scored. "
                f"Top: {ranked[0]['full_name']} ({(ranked[0]['fit_score']*100):.0f}%)"
                if ranked else "No applicants"
            ),
            "key_differentiators": [],
        },
    }

    return {
        "run_id": result.get("run_id"),
        "student_view": student_view,
        "recruiter_view": recruiter_view,
    }


def _build_recruiter_insights(recruiter_data: dict, user) -> dict:
    """Extract the requesting user's rank from recruiter results."""
    candidates = recruiter_data.get("ranked_candidates", [])
    your_rank = None
    your_score = None
    for i, c in enumerate(candidates, 1):
        if c.get("user_id") == user.id:
            your_rank = i
            your_score = c.get("composite_score", 0)
            break

    important_skills = []
    job_info = recruiter_data.get("job", {})
    for sr in job_info.get("skill_requirements", []):
        important_skills.append(sr.get("skill_name", ""))

    return {
        "total_applicants": recruiter_data.get("total_applicants", len(candidates)),
        "your_rank": your_rank,
        "your_fit_score": your_score,
        "key_differentiators": important_skills[:5],
    }
