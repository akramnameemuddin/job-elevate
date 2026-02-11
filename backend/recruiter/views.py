from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.db import transaction
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)

from accounts.models import User
from .models import Job, Application, Message

@login_required
def recruiter_dashboard(request):
    """Main dashboard view for recruiters"""
    user = request.user
    
    # Check if user is recruiter
    if user.user_type != 'recruiter':
        messages.error(request, _("Access denied. You must be a recruiter to view this page."))
        return redirect('accounts:login')
    
    # Compute initials from full name
    full_name = user.full_name.strip() if user.full_name else ""
    name_parts = full_name.split()
    if len(name_parts) >= 2:
        initials = name_parts[0][0].upper() + name_parts[-1][0].upper()
    elif len(name_parts) == 1:
        initials = name_parts[0][0].upper()
    else:
        initials = "US"
    
    # Get stats for dashboard
    active_jobs_count = Job.objects.filter(posted_by=user, status='Open').count()
    total_applicants = Application.objects.filter(job__posted_by=user).count()
    hired_applicants = Application.objects.filter(job__posted_by=user, status='Hired').count()
    
    context = {
        'user': user,
        'user_initials': initials,
        'active_jobs_count': active_jobs_count,
        'total_applicants': total_applicants,
        'hired_applicants': hired_applicants,
    }
      
    return render(request, 'recruiter_dashboard.html', context)

@login_required
def get_dashboard_stats(request):
    """API endpoint to get dashboard statistics"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    active_jobs = Job.objects.filter(posted_by=request.user, status='Open').count()
    total_applicants = Application.objects.filter(job__posted_by=request.user).count()
    hired_applicants = Application.objects.filter(job__posted_by=request.user, status='Hired').count()
    
    return JsonResponse({
        'active_jobs': active_jobs,
        'applicants': total_applicants,
        'hired': hired_applicants
    })


@login_required
def get_chart_data(request):
    """API endpoint returning data for dashboard charts"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)

    user = request.user

    # 1) Application-status breakdown (for doughnut chart)
    status_qs = (
        Application.objects.filter(job__posted_by=user)
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    status_labels = []
    status_counts = []
    for row in status_qs:
        status_labels.append(row['status'])
        status_counts.append(row['count'])

    # 2) Jobs by type (for bar chart)
    type_qs = (
        Job.objects.filter(posted_by=user)
        .values('job_type')
        .annotate(count=Count('id'))
        .order_by('job_type')
    )
    type_labels = [r['job_type'] for r in type_qs]
    type_counts = [r['count'] for r in type_qs]

    # 3) Applications over the last 30 days (for line chart)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_qs = (
        Application.objects.filter(job__posted_by=user, applied_at__gte=thirty_days_ago)
        .annotate(day=TruncDate('applied_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    daily_labels = [r['day'].strftime('%b %d') for r in daily_qs]
    daily_counts = [r['count'] for r in daily_qs]

    # 4) Hiring pipeline / funnel
    pipeline_stages = ['Applied', 'Shortlisted', 'Interview', 'Offered', 'Hired']
    pipeline_counts = []
    for stage in pipeline_stages:
        cnt = Application.objects.filter(job__posted_by=user, status=stage).count()
        pipeline_counts.append(cnt)

    # 5) Job status breakdown (Open / Closed / Paused / Filled)
    job_status_qs = (
        Job.objects.filter(posted_by=user)
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    job_status_labels = [r['status'] for r in job_status_qs]
    job_status_counts = [r['count'] for r in job_status_qs]

    return JsonResponse({
        'application_status': {'labels': status_labels, 'data': status_counts},
        'jobs_by_type': {'labels': type_labels, 'data': type_counts},
        'daily_applications': {'labels': daily_labels, 'data': daily_counts},
        'hiring_pipeline': {'labels': pipeline_stages, 'data': pipeline_counts},
        'job_status': {'labels': job_status_labels, 'data': job_status_counts},
    })

@login_required
def get_jobs(request):
    """API endpoint to get recruiter's jobs"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    jobs = Job.objects.filter(posted_by=request.user)
    
    jobs_data = []
    for job in jobs:
        # Get detailed skill requirements
        from recruiter.models import JobSkillRequirement
        skill_requirements = JobSkillRequirement.objects.filter(job=job).select_related('skill')
        
        skills_with_details = []
        for req in skill_requirements:
            skills_with_details.append({
                'name': req.skill.name,
                'proficiency': req.required_proficiency,
                'criticality': req.skill_type,  # must_have, important, nice_to_have
                'mandatory': req.is_mandatory
            })
        
        jobs_data.append({
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'type': job.job_type,
            'salary': job.salary or '',
            'experience': job.experience,
            'skills': skills_with_details,  # Now includes full details
            'description': job.description,
            'requirements': job.requirements or '',
            'status': job.status,
            'applicants': job.applicant_count,
            'created_at': job.created_at.strftime('%Y-%m-%d')
        })
    
    return JsonResponse({'jobs': jobs_data})

@login_required
@require_POST
def create_job(request):
    """Create a new job posting"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Use transaction to ensure all-or-nothing
        with transaction.atomic():
            # Extract skills data
            skills_data = data.get('skills', [])
            
            # Handle both old format (strings) and new format (objects)
            skill_names = []
            skill_objects = []
            
            for skill in skills_data:
                if isinstance(skill, dict):
                    # New format: {name, proficiency, criticality, mandatory}
                    skill_names.append(skill['name'])
                    skill_objects.append(skill)
                else:
                    # Old format: just skill name as string
                    skill_names.append(skill)
                    skill_objects.append({
                        'name': skill,
                        'proficiency': 7.0,
                        'criticality': 'important',
                        'mandatory': False
                    })
            
            # Create new job
            job = Job.objects.create(
                posted_by=request.user,
                title=data.get('title'),
                company=data.get('company'),
                location=data.get('location'),
                job_type=data.get('type'),
                salary=data.get('salary'),
                experience=data.get('experience', 0),
                skills=skill_names,  # Store simple names for backward compatibility
                description=data.get('description'),
                requirements=data.get('requirements'),
                status='Open'
            )
            
            # Create JobSkillRequirement records for detailed skill data
            from recruiter.models import JobSkillRequirement
            from assessments.models import Skill, SkillCategory
            
            # Get or create a default category for job-posted skills
            default_category, _ = SkillCategory.objects.get_or_create(
                name='General',
                defaults={'description': 'General skills'}
            )
            
            for skill_data in skill_objects:
                # Get or create skill
                skill_name = skill_data['name'].strip()
                # Use filter().first() to avoid MultipleObjectsReturned error
                skill = Skill.objects.filter(name__iexact=skill_name).first()
                if not skill:
                    skill = Skill.objects.create(
                        name=skill_name,
                        is_active=True,
                        category=default_category
                    )
                
                # Map skill_type to weight and criticality (numeric)
                skill_type = skill_data.get('criticality', 'important')
                criticality_map = {
                    'must_have': {'weight': 1.8, 'criticality': 1.0},
                    'important': {'weight': 1.2, 'criticality': 0.5},
                    'nice_to_have': {'weight': 0.8, 'criticality': 0.0}
                }
                
                config = criticality_map.get(skill_type, {'weight': 1.2, 'criticality': 0.5})
                
                # Create JobSkillRequirement
                JobSkillRequirement.objects.create(
                    job=job,
                    skill=skill,
                    required_proficiency=float(skill_data.get('proficiency', 7.0)),
                    is_mandatory=bool(skill_data.get('mandatory', False)),
                    skill_type=skill_type,
                    criticality=config['criticality'],
                    weight=config['weight']
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Job posted successfully',
            'job_id': job.id
        })
        
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error creating job: {str(e)}'
        }, status=400)

@login_required
@require_POST
def update_job(request, job_id):
    """Update an existing job posting"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    
    try:
        data = json.loads(request.body)
        
        # Use transaction to ensure all-or-nothing
        with transaction.atomic():
            # Extract skills data
            skills_data = data.get('skills', [])
            
            # Handle both old format (strings) and new format (objects)
            skill_names = []
            skill_objects = []
            
            for skill in skills_data:
                if isinstance(skill, dict):
                    skill_names.append(skill['name'])
                    skill_objects.append(skill)
                else:
                    skill_names.append(skill)
                    skill_objects.append({
                        'name': skill,
                        'proficiency': 7.0,
                        'criticality': 'important',
                        'mandatory': False
                    })
            
            # Update job fields
            job.title = data.get('title', job.title)
            job.company = data.get('company', job.company)
            job.location = data.get('location', job.location)
            job.job_type = data.get('type', job.job_type)
            job.salary = data.get('salary', job.salary)
            job.experience = data.get('experience', job.experience)
            job.skills = skill_names  # Store simple names
            job.description = data.get('description', job.description)
            job.requirements = data.get('requirements', job.requirements)
            job.status = data.get('status', job.status)
            job.save()
            
            # Update JobSkillRequirement records
            from recruiter.models import JobSkillRequirement
            from assessments.models import Skill, SkillCategory
            
            # Get or create a default category for job-posted skills
            default_category, _ = SkillCategory.objects.get_or_create(
                name='General',
                defaults={'description': 'General skills'}
            )
            
            # Delete existing requirements
            JobSkillRequirement.objects.filter(job=job).delete()
            
            # Create new requirements
            for skill_data in skill_objects:
                skill_name = skill_data['name'].strip()
                # Use filter().first() to avoid MultipleObjectsReturned error
                skill = Skill.objects.filter(name__iexact=skill_name).first()
                if not skill:
                    skill = Skill.objects.create(
                        name=skill_name,
                        is_active=True,
                        category=default_category
                    )
                
                # Map skill_type to weight and criticality (numeric)
                skill_type = skill_data.get('criticality', 'important')
                criticality_map = {
                    'must_have': {'weight': 1.8, 'criticality': 1.0},
                    'important': {'weight': 1.2, 'criticality': 0.5},
                    'nice_to_have': {'weight': 0.8, 'criticality': 0.0}
                }
                
                config = criticality_map.get(skill_type, {'weight': 1.2, 'criticality': 0.5})
                
                JobSkillRequirement.objects.create(
                    job=job,
                    skill=skill,
                    required_proficiency=float(skill_data.get('proficiency', 7.0)),
                    is_mandatory=bool(skill_data.get('mandatory', False)),
                    skill_type=skill_type,
                    criticality=config['criticality'],
                    weight=config['weight']
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Job updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error updating job: {str(e)}'
        }, status=400)

@login_required
@require_POST
def delete_job(request, job_id):
    """Delete a job posting"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    
    try:
        job.delete()
        return JsonResponse({
            'success': True,
            'message': 'Job deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting job: {str(e)}'
        }, status=400)

@login_required
def get_candidates(request, job_id=None):
    """Get candidates for all jobs or a specific job"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Filter parameters
    skills = request.GET.getlist('skills', [])
    experience = request.GET.get('experience', '')
    location = request.GET.get('location', '')
    
    # Start with all applications for this recruiter
    applications = Application.objects.filter(job__posted_by=request.user)
    
    # Filter by job if specified
    if job_id:
        applications = applications.filter(job_id=job_id)
    
    # Apply other filters
    if skills:
        # This is more complex - need to filter by applicant skills
        applications = applications.filter(applicant__technical_skills__icontains=skills[0])
        for skill in skills[1:]:
            applications = applications.filter(applicant__technical_skills__icontains=skill)
    
    if experience:
        # Parse experience range (e.g., "1-3", "5+")
        if '-' in experience:
            min_exp, max_exp = experience.split('-')
            applications = applications.filter(
                applicant__experience__gte=int(min_exp),
                applicant__experience__lte=int(max_exp)
            )
        elif '+' in experience:
            min_exp = experience.replace('+', '')
            applications = applications.filter(applicant__experience__gte=int(min_exp))
    
    if location:
        # Search in preferred_location field (synced from job preferences) and organization
        applications = applications.filter(
            Q(applicant__preferred_location__icontains=location) |
            Q(applicant__organization__icontains=location)
        )
    
    # Prepare response data with enhanced match scores
    from jobs.skill_based_matching_engine import SkillBasedJobMatcher
    
    candidates = []
    for app in applications:
        # Calculate detailed match analysis
        matcher = SkillBasedJobMatcher(app.applicant)
        match_analysis = matcher.calculate_job_match(app.job)
        
        # Determine location: prefer preferred_location, fall back to organization
        candidate_location = app.applicant.preferred_location or app.applicant.organization or 'Not specified'
        
        candidates.append({
            'id': app.id,
            'applicant_id': app.applicant.id,
            'name': app.applicant.full_name,
            'email': app.applicant.email,
            'job_title': app.job.title if job_id is None else None,
            'skills': app.applicant.get_skills_list(),
            'experience': app.applicant.experience or 0,
            'location': candidate_location,
            'match': app.match_score,
            'match_percentage': match_analysis.get('overall_score', 0),
            'eligibility_status': match_analysis.get('eligibility_status', 'Unknown'),
            'matched_skills': match_analysis.get('matched_skills_count', 0),
            'total_skills': match_analysis.get('total_required_skills', 0),
            'gap_count': match_analysis.get('gap_count', 0),
            'status': app.status,
            'applied_at': app.applied_at.strftime('%Y-%m-%d'),
            'resume_url': app.resume.url if app.resume else None
        })
    
    # Sort by match percentage (highest first)
    candidates.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    return JsonResponse({'candidates': candidates})

@login_required
@require_POST
def update_application_status(request, application_id):
    """Update the status of a job application"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    application = get_object_or_404(
        Application, 
        id=application_id, 
        job__posted_by=request.user
    )
    
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in dict(Application.APPLICATION_STATUS_CHOICES):
            return JsonResponse({
                'success': False,
                'message': 'Invalid status value'
            }, status=400)
        
        application.status = new_status
        application.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Application status updated to {new_status}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating application: {str(e)}'
        }, status=400)

@login_required
@require_POST
def update_profile(request):
    """Update recruiter profile information"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        user = request.user
        user.full_name = data.get('name', user.full_name)
        user.company_name = data.get('company', user.company_name)
        user.email = data.get('email', user.email)
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating profile: {str(e)}'
        }, status=400)

@login_required
@require_POST
def send_message(request, application_id):
    """Send a message to an applicant"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    application = get_object_or_404(
        Application, 
        id=application_id, 
        job__posted_by=request.user
    )
    
    try:
        data = json.loads(request.body)
        
        message = Message.objects.create(
            sender=request.user,
            recipient=application.applicant,
            application=application,
            subject=data.get('subject', f"Regarding your application for {application.job.title}"),
            content=data.get('content')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Message sent successfully',
            'message_id': message.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error sending message: {str(e)}'
        }, status=400)