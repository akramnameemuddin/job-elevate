"""
Job Recommendation Dashboard Views

Shows personalized job recommendations with:
1. Eligibility status (Eligible/Almost Eligible/Not Eligible)
2. Skill gap analysis
3. Matching percentage
4. Learning path suggestions
5. Apply functionality
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator

from recruiter.models import Job, Application, JobSkillRequirement
from jobs.skill_based_matching_engine import SkillBasedJobMatcher
from learning.learning_path_generator import PersonalizedLearningPathGenerator
from learning.models import SkillGap, LearningPath
from assessments.models import UserSkillProfile


@login_required
def job_recommendations_dashboard(request):
    """
    Main dashboard showing personalized job recommendations categorized by eligibility.
    """
    user = request.user
    
    # Get filter parameters
    eligibility_filter = request.GET.get('eligibility', None)
    search_query = request.GET.get('search', '')
    
    # Initialize matcher
    matcher = SkillBasedJobMatcher(user)
    
    # Get recommendations
    all_recommendations = matcher.get_recommended_jobs(
        limit=50,
        eligibility_filter=eligibility_filter
    )
    
    # Apply search filter if provided
    if search_query:
        all_recommendations = [
            rec for rec in all_recommendations
            if search_query.lower() in rec['job_title'].lower() or
               search_query.lower() in rec['company'].lower()
        ]
    
    # Categorize by eligibility
    eligible_jobs = [r for r in all_recommendations if r['eligibility_status'] == 'Eligible']
    almost_eligible_jobs = [r for r in all_recommendations if r['eligibility_status'] == 'Almost Eligible']
    not_eligible_jobs = [r for r in all_recommendations if r['eligibility_status'] == 'Not Eligible']
    
    # Get skill gap summary
    gap_summary = matcher.get_skill_gap_summary()
    
    # Get user's statistics
    verified_skills_count = UserSkillProfile.objects.filter(
        user=user,
        status='verified'
    ).count()
    
    active_learning_paths = LearningPath.objects.filter(
        user=user,
        status__in=['not_started', 'in_progress']
    ).count()
    
    stats = {
        'verified_skills': verified_skills_count,
        'eligible_jobs': len(eligible_jobs),
        'almost_eligible_jobs': len(almost_eligible_jobs),
        'not_eligible_jobs': len(not_eligible_jobs),
        'active_learning_paths': active_learning_paths,
        'total_jobs': len(all_recommendations)
    }
    
    # Pagination
    page = request.GET.get('page', 1)
    
    if eligibility_filter == 'Eligible':
        jobs_to_paginate = eligible_jobs
    elif eligibility_filter == 'Almost Eligible':
        jobs_to_paginate = almost_eligible_jobs
    elif eligibility_filter == 'Not Eligible':
        jobs_to_paginate = not_eligible_jobs
    else:
        jobs_to_paginate = all_recommendations
    
    paginator = Paginator(jobs_to_paginate, 10)
    paginated_jobs = paginator.get_page(page)
    
    context = {
        'jobs': paginated_jobs,
        'eligible_jobs': eligible_jobs[:5] if not eligibility_filter else eligible_jobs,
        'almost_eligible_jobs': almost_eligible_jobs[:5] if not eligibility_filter else almost_eligible_jobs,
        'not_eligible_jobs': not_eligible_jobs[:5] if not eligibility_filter else not_eligible_jobs,
        'gap_summary': gap_summary[:10],
        'stats': stats,
        'eligibility_filter': eligibility_filter,
        'search_query': search_query
    }
    
    return render(request, 'jobs/recommendations_dashboard.html', context)


@login_required
def job_detail_with_analysis(request, job_id):
    """
    Detailed job view with comprehensive skill analysis.
    """
    job = get_object_or_404(Job, id=job_id, status='Open')
    user = request.user
    
    # Calculate match analysis
    matcher = SkillBasedJobMatcher(user)
    match_analysis = matcher.calculate_job_match(job)
    
    # Check if user has already applied
    has_applied = Application.objects.filter(
        job=job,
        applicant=user
    ).exists()
    
    # Get or create skill gaps for this job
    skill_gaps = SkillGap.objects.filter(
        user=user,
        related_job=job
    ).select_related('skill')
    
    # Get relevant learning paths
    if match_analysis['skill_gaps']:
        skill_ids = [gap['skill_id'] for gap in match_analysis['skill_gaps']]
        learning_paths = LearningPath.objects.filter(
            user=user,
            skill_gap__skill_id__in=skill_ids,
            status__in=['not_started', 'in_progress']
        ).select_related('skill_gap__skill')
    else:
        learning_paths = []
    
    context = {
        'job': job,
        'match_analysis': match_analysis,
        'has_applied': has_applied,
        'skill_gaps': skill_gaps,
        'learning_paths': learning_paths,
        'can_apply': match_analysis['can_apply'] and not has_applied
    }
    
    return render(request, 'jobs/job_detail_analysis.html', context)


@login_required
def generate_learning_path_for_job(request, job_id):
    """
    Generate personalized learning paths for all skill gaps in a job.
    """
    job = get_object_or_404(Job, id=job_id, status='Open')
    user = request.user
    
    if request.method == 'POST':
        # Generate learning paths
        generator = PersonalizedLearningPathGenerator(user)
        
        try:
            learning_paths = generator.generate_for_job(job, create_paths=True)
            
            if learning_paths:
                messages.success(
                    request,
                    f"Created {len(learning_paths)} personalized learning path(s) to help you qualify for this job!"
                )
            else:
                messages.info(
                    request,
                    "You already meet all requirements for this job, or no learning paths needed!"
                )
            
            return redirect('jobs:job_detail_analysis', job_id=job_id)
            
        except Exception as e:
            messages.error(request, f"Error generating learning paths: {str(e)}")
            return redirect('jobs:job_detail_analysis', job_id=job_id)
    
    return redirect('jobs:job_detail_analysis', job_id=job_id)


@login_required
def skill_gap_analysis(request):
    """
    Comprehensive skill gap analysis across all jobs.
    """
    user = request.user
    matcher = SkillBasedJobMatcher(user)
    
    # Get skill gap summary
    gap_summary = matcher.get_skill_gap_summary()
    
    # Get all skill gaps with related jobs
    skill_gaps = SkillGap.objects.filter(
        user=user,
        is_addressed=False
    ).select_related('skill', 'related_job').order_by('-priority_score')
    
    # Group by priority
    critical_gaps = skill_gaps.filter(priority='critical')
    high_gaps = skill_gaps.filter(priority='high')
    moderate_gaps = skill_gaps.filter(priority='moderate')
    low_gaps = skill_gaps.filter(priority='low')
    
    # Get learning paths
    learning_paths = LearningPath.objects.filter(
        user=user,
        status__in=['not_started', 'in_progress']
    ).select_related('skill_gap__skill').prefetch_related('courses')
    
    context = {
        'gap_summary': gap_summary,
        'critical_gaps': critical_gaps,
        'high_gaps': high_gaps,
        'moderate_gaps': moderate_gaps,
        'low_gaps': low_gaps,
        'learning_paths': learning_paths,
        'total_gaps': skill_gaps.count()
    }
    
    return render(request, 'jobs/skill_gap_analysis.html', context)


@login_required
def apply_to_job(request, job_id):
    """
    Apply to a job (only if eligible or almost eligible).
    """
    job = get_object_or_404(Job, id=job_id, status='Open')
    user = request.user
    
    # Check eligibility
    matcher = SkillBasedJobMatcher(user)
    match_analysis = matcher.calculate_job_match(job)
    
    if not match_analysis['can_apply']:
        messages.error(
            request,
            "You don't meet the minimum requirements for this job. "
            "Complete the recommended learning paths first."
        )
        return redirect('jobs:job_detail_analysis', job_id=job_id)
    
    # Check if already applied
    if Application.objects.filter(job=job, applicant=user).exists():
        messages.warning(request, "You have already applied to this job.")
        return redirect('jobs:job_detail_analysis', job_id=job_id)
    
    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '')
        resume = request.FILES.get('resume', None)
        
        # Create application
        application = Application.objects.create(
            job=job,
            applicant=user,
            cover_letter=cover_letter,
            resume=resume,
            match_score=int(match_analysis['overall_score']),
            status='Applied'
        )
        
        messages.success(
            request,
            f"Application submitted successfully! Match score: {match_analysis['overall_score']:.1f}%"
        )
        
        return redirect('jobs:job_detail_analysis', job_id=job_id)
    
    context = {
        'job': job,
        'match_analysis': match_analysis
    }
    
    return render(request, 'jobs/apply_to_job.html', context)


@login_required
def my_applications(request):
    """
    View all user's job applications with their match scores.
    """
    user = request.user
    
    applications = Application.objects.filter(
        applicant=user
    ).select_related('job').order_by('-applied_at')
    
    # Add match analysis for each application
    matcher = SkillBasedJobMatcher(user)
    
    applications_with_analysis = []
    for app in applications:
        match_analysis = matcher.calculate_job_match(app.job)
        applications_with_analysis.append({
            'application': app,
            'match_analysis': match_analysis
        })
    
    context = {
        'applications_with_analysis': applications_with_analysis,
        'total_applications': applications.count()
    }
    
    return render(request, 'jobs/my_applications.html', context)


@login_required
def learning_paths_dashboard(request):
    """
    Dashboard for managing all learning paths.
    """
    user = request.user
    
    # Get learning paths by status
    not_started = LearningPath.objects.filter(
        user=user,
        status='not_started'
    ).select_related('skill_gap__skill', 'skill_gap__related_job').prefetch_related('courses')
    
    in_progress = LearningPath.objects.filter(
        user=user,
        status='in_progress'
    ).select_related('skill_gap__skill', 'skill_gap__related_job').prefetch_related('courses')
    
    completed = LearningPath.objects.filter(
        user=user,
        status='completed'
    ).select_related('skill_gap__skill', 'skill_gap__related_job').prefetch_related('courses')
    
    # Statistics
    stats = {
        'total_paths': not_started.count() + in_progress.count() + completed.count(),
        'not_started': not_started.count(),
        'in_progress': in_progress.count(),
        'completed': completed.count(),
        'total_hours': sum(p.estimated_hours for p in in_progress) + sum(p.estimated_hours for p in not_started)
    }
    
    context = {
        'not_started_paths': not_started,
        'in_progress_paths': in_progress,
        'completed_paths': completed,
        'stats': stats
    }
    
    return render(request, 'learning/learning_paths_dashboard.html', context)


@login_required
def start_learning_path(request, path_id):
    """
    Start a learning path.
    """
    learning_path = get_object_or_404(LearningPath, id=path_id, user=request.user)
    
    if learning_path.status == 'not_started':
        learning_path.status = 'in_progress'
        learning_path.started_at = timezone.now()
        learning_path.save()
        
        messages.success(request, f"Started learning path: {learning_path.title}")
    
    return redirect('learning:learning_path_detail', path_id=path_id)


@login_required
def complete_learning_path(request, path_id):
    """
    Mark learning path as completed and suggest reassessment.
    """
    learning_path = get_object_or_404(LearningPath, id=path_id, user=request.user)
    
    if request.method == 'POST':
        learning_path.status = 'completed'
        learning_path.completed_at = timezone.now()
        learning_path.progress_percentage = 100
        learning_path.save()
        
        # Mark skill gap as addressed
        if learning_path.skill_gap:
            learning_path.skill_gap.is_addressed = True
            learning_path.skill_gap.save()
        
        messages.success(
            request,
            f"Congratulations on completing '{learning_path.title}'! "
            f"Retake the assessment to update your verified proficiency."
        )
        
        return redirect('assessments:retake_assessment', skill_id=learning_path.skill_gap.skill_id)
    
    return redirect('learning:learning_path_detail', path_id=path_id)
