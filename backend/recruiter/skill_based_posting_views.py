"""
Recruiter Job Posting Views with Skill Requirements

Allows recruiters to:
1. Post jobs with detailed skill requirements
2. Set minimum proficiency levels per skill
3. Designate skills as mandatory/critical/optional
4. Assign skill weights for matching
5. View candidate matches with verified proficiency
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
import json

from recruiter.models import Job, Application, JobSkillRequirement, UserJobFitScore
from assessments.models import Skill, SkillCategory, UserSkillProfile
from accounts.models import User
from jobs.skill_based_matching_engine import SkillBasedJobMatcher


def user_is_recruiter(user):
    """Check if user is a recruiter."""
    return user.is_authenticated and user.user_type == 'recruiter'


@login_required
def post_job_with_skills(request):
    """
    Create new job posting with comprehensive skill requirements.
    """
    if not user_is_recruiter(request.user):
        messages.error(request, "Only recruiters can post jobs.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        # Basic job information
        title = request.POST.get('title')
        company = request.POST.get('company')
        location = request.POST.get('location')
        job_type = request.POST.get('job_type')
        salary = request.POST.get('salary', '')
        experience = int(request.POST.get('experience', 0))
        description = request.POST.get('description')
        requirements = request.POST.get('requirements', '')
        
        # Create job
        job = Job.objects.create(
            title=title,
            company=company,
            location=location,
            job_type=job_type,
            salary=salary,
            experience=experience,
            description=description,
            requirements=requirements,
            posted_by=request.user,
            status='Open',
            skills=[]  # Will be populated from JobSkillRequirement
        )
        
        # Process skill requirements
        skill_data = json.loads(request.POST.get('skills_data', '[]'))
        
        for skill_req in skill_data:
            skill_id = skill_req.get('skill_id')
            required_proficiency = float(skill_req.get('required_proficiency', 5.0))
            is_mandatory = skill_req.get('is_mandatory', False)
            skill_type = skill_req.get('skill_type', 'important')
            weight = float(skill_req.get('weight', 1.0))
            description_text = skill_req.get('description', '')
            
            # Determine criticality based on skill_type
            criticality_map = {
                'must_have': 1.0,
                'important': 0.7,
                'nice_to_have': 0.3
            }
            criticality = criticality_map.get(skill_type, 0.7)
            
            try:
                skill = Skill.objects.get(id=skill_id)
                
                # Use get_or_create to prevent duplicate requirements
                JobSkillRequirement.objects.get_or_create(
                    job=job,
                    skill=skill,
                    defaults={
                        'required_proficiency': required_proficiency,
                        'criticality': criticality,
                        'is_mandatory': is_mandatory,
                        'skill_type': skill_type,
                        'weight': weight,
                        'description': description_text
                    }
                )
                
            except Skill.DoesNotExist:
                pass
        
        messages.success(
            request,
            f"Job '{title}' posted successfully with {len(skill_data)} skill requirement(s)!"
        )
        
        return redirect('recruiter:job_detail', job_id=job.id)
    
    # GET request - show form
    categories = SkillCategory.objects.prefetch_related('skills').all()
    
    context = {
        'categories': categories,
        'job_types': Job.JOB_TYPE_CHOICES
    }
    
    return render(request, 'recruiter/post_job_with_skills.html', context)


@login_required
def edit_job_skills(request, job_id):
    """
    Edit skill requirements for an existing job.
    """
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    
    if request.method == 'POST':
        # Delete existing requirements
        JobSkillRequirement.objects.filter(job=job).delete()
        
        # Add new requirements
        skill_data = json.loads(request.POST.get('skills_data', '[]'))
        
        for skill_req in skill_data:
            skill_id = skill_req.get('skill_id')
            required_proficiency = float(skill_req.get('required_proficiency', 5.0))
            is_mandatory = skill_req.get('is_mandatory', False)
            skill_type = skill_req.get('skill_type', 'important')
            weight = float(skill_req.get('weight', 1.0))
            description_text = skill_req.get('description', '')
            
            criticality_map = {
                'must_have': 1.0,
                'important': 0.7,
                'nice_to_have': 0.3
            }
            criticality = criticality_map.get(skill_type, 0.7)
            
            try:
                skill = Skill.objects.get(id=skill_id)
                
                # Check if requirement already exists to avoid duplicates
                JobSkillRequirement.objects.get_or_create(
                    job=job,
                    skill=skill,
                    defaults={
                        'required_proficiency': required_proficiency,
                        'criticality': criticality,
                        'is_mandatory': is_mandatory,
                        'skill_type': skill_type,
                        'weight': weight,
                        'description': description_text
                    }
                )
                
            except Skill.DoesNotExist:
                pass
        
        messages.success(request, "Skill requirements updated successfully!")
        return redirect('recruiter:job_detail', job_id=job.id)
    
    # GET request - show form with existing requirements
    existing_requirements = JobSkillRequirement.objects.filter(
        job=job
    ).select_related('skill')
    
    categories = SkillCategory.objects.prefetch_related('skills').all()
    
    context = {
        'job': job,
        'existing_requirements': existing_requirements,
        'categories': categories,
        'job_types': Job.JOB_TYPE_CHOICES
    }
    
    return render(request, 'recruiter/edit_job_skills.html', context)


@login_required
def view_job_applications_with_scores(request, job_id):
    """
    View all applications for a job with skill match analysis.
    """
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    
    applications = Application.objects.filter(
        job=job
    ).select_related('applicant').order_by('-match_score', '-applied_at')
    
    # Calculate detailed match for each applicant
    applications_with_analysis = []
    
    for app in applications:
        matcher = SkillBasedJobMatcher(app.applicant)
        match_analysis = matcher.calculate_job_match(job)
        
        applications_with_analysis.append({
            'application': app,
            'match_analysis': match_analysis,
            'applicant': app.applicant
        })
    
    # Filter by eligibility if requested
    eligibility_filter = request.GET.get('eligibility', None)
    if eligibility_filter:
        applications_with_analysis = [
            a for a in applications_with_analysis
            if a['match_analysis']['eligibility_status'] == eligibility_filter
        ]
    
    # Statistics
    stats = {
        'total_applications': applications.count(),
        'avg_match_score': applications.aggregate(Avg('match_score'))['match_score__avg'] or 0,
        'eligible_count': len([a for a in applications_with_analysis if a['match_analysis']['eligibility_status'] == 'Eligible']),
        'almost_eligible_count': len([a for a in applications_with_analysis if a['match_analysis']['eligibility_status'] == 'Almost Eligible']),
        'not_eligible_count': len([a for a in applications_with_analysis if a['match_analysis']['eligibility_status'] == 'Not Eligible'])
    }
    
    context = {
        'job': job,
        'applications_with_analysis': applications_with_analysis,
        'stats': stats,
        'eligibility_filter': eligibility_filter
    }
    
    return render(request, 'recruiter/job_applications_analysis.html', context)


@login_required
def candidate_profile_with_skills(request, user_id, job_id):
    """
    View candidate profile with detailed skill analysis for specific job.
    """
    if not user_is_recruiter(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboard:index')
    
    candidate = get_object_or_404(User, id=user_id)
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    
    # Get match analysis
    matcher = SkillBasedJobMatcher(candidate)
    match_analysis = matcher.calculate_job_match(job)
    
    # Get candidate's verified skills
    verified_skills = UserSkillProfile.objects.filter(
        user=candidate,
        status='verified'
    ).select_related('skill').order_by('-verified_level')
    
    # Get application if exists
    application = Application.objects.filter(
        job=job,
        applicant=candidate
    ).first()
    
    context = {
        'candidate': candidate,
        'job': job,
        'match_analysis': match_analysis,
        'verified_skills': verified_skills,
        'application': application
    }
    
    return render(request, 'recruiter/candidate_profile_analysis.html', context)


@login_required
def find_qualified_candidates(request, job_id):
    """
    Search for candidates who meet job requirements (proactive recruitment).
    """
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    
    # Get job skill requirements
    requirements = JobSkillRequirement.objects.filter(job=job).select_related('skill')
    
    if not requirements.exists():
        messages.warning(request, "Please add skill requirements to this job first.")
        return redirect('recruiter:edit_job_skills', job_id=job_id)
    
    # Find candidates with verified skills matching requirements
    skill_ids = [req.skill_id for req in requirements]
    
    # Get users who have verified skills in required areas
    potential_candidates = User.objects.filter(
        user_type__in=['student', 'professional'],
        skill_profiles__skill_id__in=skill_ids,
        skill_profiles__status='verified'
    ).distinct()
    
    # Exclude users who already applied
    applied_user_ids = Application.objects.filter(job=job).values_list('applicant_id', flat=True)
    potential_candidates = potential_candidates.exclude(id__in=applied_user_ids)
    
    # Calculate match for each candidate
    candidates_with_analysis = []
    
    for candidate in potential_candidates[:50]:  # Limit to 50 for performance
        matcher = SkillBasedJobMatcher(candidate)
        match_analysis = matcher.calculate_job_match(job)
        
        # Only include candidates who are Eligible or Almost Eligible
        if match_analysis['eligibility_status'] in ['Eligible', 'Almost Eligible']:
            candidates_with_analysis.append({
                'candidate': candidate,
                'match_analysis': match_analysis
            })
    
    # Sort by match score
    candidates_with_analysis.sort(key=lambda x: x['match_analysis']['overall_score'], reverse=True)
    
    context = {
        'job': job,
        'candidates_with_analysis': candidates_with_analysis,
        'total_qualified': len(candidates_with_analysis)
    }
    
    return render(request, 'recruiter/qualified_candidates.html', context)


@login_required
def recruiter_dashboard_enhanced(request):
    """
    Enhanced recruiter dashboard with skill-based insights.
    """
    if not user_is_recruiter(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboard:index')
    
    # Get recruiter's jobs
    jobs = Job.objects.filter(posted_by=request.user).annotate(
        application_count=Count('applications')
    ).order_by('-created_at')
    
    # Statistics
    total_jobs = jobs.count()
    open_jobs = jobs.filter(status='Open').count()
    total_applications = Application.objects.filter(job__posted_by=request.user).count()
    
    # Get recent applications with match analysis
    recent_applications = Application.objects.filter(
        job__posted_by=request.user
    ).select_related('job', 'applicant').order_by('-applied_at')[:10]
    
    applications_with_scores = []
    for app in recent_applications:
        matcher = SkillBasedJobMatcher(app.applicant)
        match_analysis = matcher.calculate_job_match(app.job)
        
        applications_with_scores.append({
            'application': app,
            'match_score': match_analysis['overall_score'],
            'eligibility': match_analysis['eligibility_status']
        })
    
    context = {
        'jobs': jobs,
        'stats': {
            'total_jobs': total_jobs,
            'open_jobs': open_jobs,
            'total_applications': total_applications,
            'avg_applications_per_job': total_applications / total_jobs if total_jobs > 0 else 0
        },
        'recent_applications': applications_with_scores
    }
    
    return render(request, 'recruiter/dashboard_enhanced.html', context)
