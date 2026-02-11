"""
Agents app views
================
Provides three views:
1. career_guidance_view   – students / professionals
2. recruiter_agent_view   – recruiters
3. multi_agent_demo_view  – full end-to-end multi-agent pipeline (both roles)
"""
from __future__ import annotations

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from recruiter.models import Job

from .models import AgentMessage, AgentRunLog
from .orchestrator import Orchestrator

logger = logging.getLogger(__name__)


def _is_recruiter(user):
    return getattr(user, 'user_type', None) == 'recruiter'


@login_required
def career_guidance_view(request):
    """
    Career coaching view for students and professionals.
    Recruiters are redirected away.
    GET  → renders the template (with optional ?job_id=<id>).
    POST → triggers the orchestrator career flow and returns JSON.
    """
    if _is_recruiter(request.user):
        return HttpResponseForbidden("This page is only for students and professionals.")

    if request.method == "POST":
        target_job_id = request.POST.get("job_id") or request.GET.get("job_id")
        target_job_id = int(target_job_id) if target_job_id else None

        try:
            orchestrator = Orchestrator()
            result = orchestrator.run_career_flow(
                user_id=request.user.id,
                target_job_id=target_job_id,
            )
        except Exception as exc:
            logger.exception("Career flow error")
            result = {"error": str(exc)}

        return JsonResponse(result, safe=False)

    # GET – render template
    job_id = request.GET.get("job_id")
    target_job = None
    if job_id:
        target_job = Job.objects.filter(pk=job_id).first()

    # List all open jobs for the dropdown
    available_jobs = Job.objects.filter(status="Open").order_by("-created_at")[:30]

    # Show recent runs for this user
    recent_runs = (
        AgentRunLog.objects.filter(user=request.user, run_type="career_flow")
        .order_by("-started_at")[:5]
    )

    return render(request, "agents/career_guidance.html", {
        "target_job": target_job,
        "available_jobs": available_jobs,
        "recent_runs": recent_runs,
    })


@login_required
def recruiter_agent_view(request):
    """
    Recruiter view for ranking applicants.
    Only accessible to users with user_type='recruiter'.
    GET  → renders template (expects ?job_id=<id>).
    POST → triggers the recruiter flow and returns JSON.
    """
    if not _is_recruiter(request.user):
        return HttpResponseForbidden("This page is only for recruiters.")

    if request.method == "POST":
        job_id = request.POST.get("job_id") or request.GET.get("job_id")
        if not job_id:
            return JsonResponse({"error": "job_id is required"}, status=400)

        try:
            orchestrator = Orchestrator()
            result = orchestrator.run_recruiter_flow(job_id=int(job_id))
        except Exception as exc:
            logger.exception("Recruiter flow error")
            result = {"error": str(exc)}

        return JsonResponse(result, safe=False)

    # GET
    job_id = request.GET.get("job_id")
    job = None
    if job_id:
        job = Job.objects.filter(pk=job_id, posted_by=request.user).first()

    # List recruiter's jobs
    my_jobs = Job.objects.filter(posted_by=request.user).order_by("-created_at")[:20]

    recent_runs = (
        AgentRunLog.objects.filter(user=request.user, run_type="recruiter_flow")
        .order_by("-started_at")[:5]
    )

    return render(request, "agents/recruiter_agent.html", {
        "job": job,
        "my_jobs": my_jobs,
        "recent_runs": recent_runs,
    })


@login_required
def multi_agent_demo_view(request):
    """
    Full multi-agent demo view.
    GET  → renders template with a job selector.
    POST → triggers the full flow and returns JSON with both student and recruiter views.
    """
    if request.method == "POST":
        job_id = request.POST.get("job_id") or request.GET.get("job_id")
        if not job_id:
            return JsonResponse({"error": "job_id is required"}, status=400)

        try:
            orchestrator = Orchestrator()
            result = orchestrator.run_full_multi_agent_flow(
                user_id=request.user.id,
                job_id=int(job_id),
            )
        except Exception as exc:
            logger.exception("Multi-agent flow error")
            result = {"error": str(exc)}

        return JsonResponse(result, safe=False)

    # GET – job selector + recent runs
    jobs = Job.objects.filter(status="Open").order_by("-created_at")[:30]

    recent_runs = (
        AgentRunLog.objects.filter(run_type="full_multi_agent")
        .order_by("-started_at")[:10]
    )

    # Fetch messages for the latest run (if any) to display timeline
    latest_run = recent_runs.first() if recent_runs.exists() else None
    messages = []
    if latest_run:
        messages = list(
            latest_run.messages.order_by("created_at").values(
                "sender_agent", "receiver_agent", "intent", "created_at"
            )
        )

    return render(request, "agents/multi_agent_demo.html", {
        "jobs": jobs,
        "recent_runs": recent_runs,
        "latest_run": latest_run,
        "messages": messages,
    })


@login_required
def agent_run_detail_view(request, run_id):
    """API endpoint returning full detail of a specific agent run."""
    run = get_object_or_404(AgentRunLog, pk=run_id)
    messages = list(
        run.messages.order_by("created_at").values(
            "id", "sender_agent", "receiver_agent", "intent", "payload", "created_at"
        )
    )
    return JsonResponse({
        "run_id": run.id,
        "run_type": run.run_type,
        "status": run.status,
        "started_at": str(run.started_at),
        "completed_at": str(run.completed_at) if run.completed_at else None,
        "result": run.result,
        "messages": messages,
    })
