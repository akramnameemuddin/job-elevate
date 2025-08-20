from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import json

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
def get_jobs(request):
    """API endpoint to get recruiter's jobs"""
    if request.user.user_type != 'recruiter':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    jobs = Job.objects.filter(posted_by=request.user)
    
    jobs_data = []
    for job in jobs:
        jobs_data.append({
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'type': job.job_type,
            'salary': job.salary or '',
            'experience': job.experience,
            'skills': job.skills,
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
        
        # Create new job
        job = Job.objects.create(
            posted_by=request.user,
            title=data.get('title'),
            company=data.get('company'),
            location=data.get('location'),
            job_type=data.get('type'),
            salary=data.get('salary'),
            experience=data.get('experience', 0),
            skills=data.get('skills', []),
            description=data.get('description'),
            requirements=data.get('requirements'),
            status='Open'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Job posted successfully',
            'job_id': job.id
        })
        
    except Exception as e:
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
        
        # Update job fields
        job.title = data.get('title', job.title)
        job.company = data.get('company', job.company)
        job.location = data.get('location', job.location)
        job.job_type = data.get('type', job.job_type)
        job.salary = data.get('salary', job.salary)
        job.experience = data.get('experience', job.experience)
        job.skills = data.get('skills', job.skills)
        job.description = data.get('description', job.description)
        job.requirements = data.get('requirements', job.requirements)
        job.status = data.get('status', job.status)
        job.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Job updated successfully'
        })
        
    except Exception as e:
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
        # Search for location in user profile
        applications = applications.filter(applicant__organization__icontains=location)
    
    # Prepare response data
    candidates = []
    for app in applications:
        candidates.append({
            'id': app.id,
            'name': app.applicant.full_name,
            'job_title': app.job.title if job_id is None else None,
            'skills': app.applicant.get_skills_list(),
            'experience': app.applicant.experience or 0,
            'location': app.applicant.organization or 'Not specified',
            'match': app.match_score,
            'status': app.status,
            'applied_at': app.applied_at.strftime('%Y-%m-%d'),
            'resume_url': app.resume.url if app.resume else None
        })
    
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