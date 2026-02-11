"""
Views for AI-powered resume tailoring.
Flow: select resume → AI analyses job → user reviews suggestions → apply & download.
"""
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from recruiter.models import Job
from .ai_service import (
    apply_suggestions_to_resume,
    compute_keyword_match,
    generate_ai_suggestions,
)
from .models import Resume, TailoredResume

logger = logging.getLogger(__name__)


@login_required
def tailor_for_job(request, job_id):
    """
    Entry point: user picks a base resume (or we auto-select) then the
    AI agent analyses the resume vs. the job and creates a TailoredResume.
    """
    job = get_object_or_404(Job, id=job_id, status='Open')
    user = request.user

    # If user already has a tailored resume for this job, go straight to review
    existing = TailoredResume.objects.filter(user=user, job=job).first()
    if existing:
        return redirect('resume_builder:ai_review', tailored_id=existing.id)

    # Get user's resumes
    user_resumes = Resume.objects.filter(user=user)

    if request.method == 'POST':
        resume_id = request.POST.get('resume_id')
        base_resume = None
        if resume_id:
            base_resume = Resume.objects.filter(id=resume_id, user=user).first()

        # Compute before-score
        kw = compute_keyword_match(user, job)

        # Generate AI suggestions
        suggestions = generate_ai_suggestions(user, job, base_resume)

        # Create TailoredResume
        tailored = TailoredResume.objects.create(
            user=user,
            base_resume=base_resume,
            job=job,
            status='reviewed',
            suggestions=suggestions,
            match_score_before=kw['score'],
            keywords_matched=kw['matched'],
            keywords_missing=kw['missing'],
        )

        return redirect('resume_builder:ai_review', tailored_id=tailored.id)

    # GET: show resume selection page
    context = {
        'job': job,
        'user_resumes': user_resumes,
    }
    return render(request, 'resume_builder/select_resume.html', context)


@login_required
def ai_review(request, tailored_id):
    """
    Show the AI suggestions for the user to accept/reject, along with
    before/after match scores and keyword analysis.
    """
    tailored = get_object_or_404(TailoredResume, id=tailored_id, user=request.user)
    job = tailored.job
    user = request.user

    # Build user's current resume data for the side-by-side preview
    skills = user.get_skills_list()
    work_experience = user.get_work_experience() if hasattr(user, 'get_work_experience') else []
    projects = user.get_projects() if hasattr(user, 'get_projects') else []
    certifications = user.get_certifications() if hasattr(user, 'get_certifications') else []

    # Categorise suggestions by priority
    suggestions = tailored.suggestions or []
    high = [s for s in suggestions if s.get('priority') == 'high']
    medium = [s for s in suggestions if s.get('priority') == 'medium']
    low = [s for s in suggestions if s.get('priority') == 'low']

    context = {
        'tailored': tailored,
        'job': job,
        'suggestions': suggestions,
        'high_priority': high,
        'medium_priority': medium,
        'low_priority': low,
        'counts': tailored.suggestion_counts,
        'skills': skills,
        'work_experience': work_experience,
        'projects': projects,
        'certifications': certifications,
    }
    return render(request, 'resume_builder/ai_review.html', context)


@login_required
@require_POST
def accept_suggestion(request, tailored_id):
    """AJAX: Toggle a single suggestion accepted / rejected."""
    tailored = get_object_or_404(TailoredResume, id=tailored_id, user=request.user)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    suggestion_id = data.get('suggestion_id')
    accepted = data.get('accepted')  # True / False / None (reset)

    updated = False
    for s in tailored.suggestions:
        if s.get('id') == suggestion_id:
            s['accepted'] = accepted
            updated = True
            break

    if not updated:
        return JsonResponse({'error': 'Suggestion not found'}, status=404)

    tailored.save()
    return JsonResponse({
        'ok': True,
        'counts': tailored.suggestion_counts,
    })


@login_required
@require_POST
def accept_all_suggestions(request, tailored_id):
    """Accept all suggestions at once."""
    tailored = get_object_or_404(TailoredResume, id=tailored_id, user=request.user)

    for s in tailored.suggestions:
        s['accepted'] = True
    tailored.save()

    # Support both AJAX and form POST
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'ok': True,
            'counts': tailored.suggestion_counts,
        })

    messages.success(request, 'All suggestions accepted!')
    return redirect('resume_builder:ai_review', tailored_id=tailored.id)


@login_required
@require_POST
def apply_and_finalize(request, tailored_id):
    """
    Apply accepted suggestions, compute the after-match score, and
    mark the tailored resume as applied. Then redirect to the final view.
    """
    tailored = get_object_or_404(TailoredResume, id=tailored_id, user=request.user)
    user = request.user

    result = apply_suggestions_to_resume(user, tailored)

    tailored.tailored_skills = result['tailored_skills']
    tailored.tailored_objective = result['tailored_objective']
    tailored.tailored_experience = result['tailored_experience']
    tailored.tailored_projects = result['tailored_projects']
    tailored.match_score_after = result['match_score_after']
    tailored.keywords_matched = result['keywords_matched']
    tailored.keywords_missing = result['keywords_missing']
    tailored.status = 'applied'
    tailored.save()

    messages.success(request, 'Suggestions applied! Your tailored resume is ready.')
    return redirect('resume_builder:ai_review', tailored_id=tailored.id)


@login_required
def regenerate_suggestions(request, tailored_id):
    """Re-run the AI agent to get fresh suggestions."""
    tailored = get_object_or_404(TailoredResume, id=tailored_id, user=request.user)

    suggestions = generate_ai_suggestions(request.user, tailored.job, tailored.base_resume)
    kw = compute_keyword_match(request.user, tailored.job)

    tailored.suggestions = suggestions
    tailored.status = 'reviewed'
    tailored.match_score_before = kw['score']
    tailored.keywords_matched = kw['matched']
    tailored.keywords_missing = kw['missing']
    tailored.save()

    messages.info(request, 'AI agent generated fresh suggestions.')
    return redirect('resume_builder:ai_review', tailored_id=tailored.id)
