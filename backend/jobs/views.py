from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, F
from django.contrib import messages
from django.utils import timezone
import json
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from accounts.models import User
from recruiter.models import Job, Application
from .models import JobView, JobBookmark, UserJobPreference, JobRecommendation, UserSimilarity
from .forms import UserJobPreferenceForm
from jobs.recommendation_engine import HybridRecommender
from dashboard.notifications import notify_job_application, notify_application_status

logger = logging.getLogger(__name__)
recommender = HybridRecommender()

@login_required
def job_listings(request):
    """Display job listings with filtering, recommendations, bookmarks, and applications"""
    if request.user.user_type == 'recruiter':
        return redirect('recruiter:dashboard')
    
    # Get all available jobs with basic filtering
    jobs = Job.objects.filter(status='Open').select_related().order_by('-created_at')
    
    # Apply search and filter parameters
    search_query = request.GET.get('search', '').strip()
    location_filter = request.GET.get('location', '').strip()
    job_type_filter = request.GET.get('job_type', '').strip()
    
    # Apply filters if provided
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(requirements__icontains=search_query)
        )
    
    if location_filter:
        jobs = jobs.filter(location__icontains=location_filter)
    
    if job_type_filter:
        jobs = jobs.filter(job_type=job_type_filter)
    
    # Get personalized recommendations (limit to top recommendations)
    recommended_jobs = []
    try:
        all_recommendations = recommender.recommend_jobs(request.user)
        recommended_jobs = [rec for rec in all_recommendations if rec.get('score', 0) > 0.3][:6]
    except Exception as e:
        logger.error(f"Error getting recommendations for user {request.user.id}: {str(e)}")
        recommended_jobs = []
    
    # Get user's bookmarked jobs with job details
    bookmarked_jobs = JobBookmark.objects.filter(
        user=request.user
    ).select_related('job').order_by('-bookmarked_at')
    
    # Get bookmarked job IDs for quick lookup
    bookmarked_job_ids = list(bookmarked_jobs.values_list('job_id', flat=True))
    
    # Get user's job applications with job details
    applied_jobs = Application.objects.filter(
        applicant=request.user
    ).select_related('job').order_by('-applied_at')
    
    # Pagination for main job listings
    paginator = Paginator(jobs, 20)  # Show 20 jobs per page
    page_number = request.GET.get('page')
    try:
        jobs_page = paginator.page(page_number)
    except PageNotAnInteger:
        jobs_page = paginator.page(1)
    except EmptyPage:
        jobs_page = paginator.page(paginator.num_pages)
    
    # Get unique locations for the filter dropdown
    all_locations = Job.objects.filter(
        status='Open'
    ).values_list('location', flat=True).distinct().order_by('location')
    
    # Context for the template
    context = {
        'jobs': jobs_page,
        'recommended_jobs': recommended_jobs,
        'bookmarked_jobs': bookmarked_jobs,
        'applied_jobs': applied_jobs,
        'bookmarked_job_ids': bookmarked_job_ids,
        'all_locations': [loc for loc in all_locations if loc],  # Filter out empty locations
        'search_query': search_query,
        'location_filter': location_filter,
        'job_type_filter': job_type_filter,
        'total_jobs': jobs.count(),
        'has_filters': bool(search_query or location_filter or job_type_filter),
    }
    
    return render(request, 'jobs/job_listings.html', context)
@login_required
def job_detail(request, job_id):
    """Display detailed job information"""
    job = get_object_or_404(Job, id=job_id, status='Open')

    # Track that the user viewed this job
    recommender.track_job_view(request.user, job)

    # Check if the user has applied to this job
    already_applied = Application.objects.filter(
        job=job,
        applicant=request.user
    ).exists()

    # Check if the job is bookmarked
    is_bookmarked = JobBookmark.objects.filter(
        job=job,
        user=request.user
    ).exists()

    # Get company description from recruiter profile
    company_description = None
    try:
        # First try to get from recruiter profile
        if hasattr(job.posted_by, 'recruiterprofile'):
            company_description = job.posted_by.recruiterprofile.company_description
        # Fallback to user's company description field
        elif job.posted_by.company_description:
            company_description = job.posted_by.company_description
    except Exception:
        company_description = None

    # Get similar jobs using improved algorithm
    similar_jobs = []
    try:
        # Get all open jobs except current one
        all_jobs = Job.objects.filter(status='Open').exclude(id=job_id)

        # Calculate similarity scores for better recommendations
        job_skills_set = set(job.skills) if job.skills else set()

        similar_jobs_with_scores = []
        for similar_job in all_jobs:
            similar_skills_set = set(similar_job.skills) if similar_job.skills else set()

            # Calculate similarity based on multiple factors
            similarity_score = 0

            # Skills similarity (primary factor)
            if job_skills_set and similar_skills_set:
                overlap = len(job_skills_set.intersection(similar_skills_set))
                if overlap > 0:
                    similarity_score += overlap / len(job_skills_set.union(similar_skills_set)) * 0.7

            # Job type similarity
            if job.job_type == similar_job.job_type:
                similarity_score += 0.2

            # Location similarity (basic)
            if job.location.lower() == similar_job.location.lower():
                similarity_score += 0.1

            # Only include jobs with decent similarity
            if similarity_score > 0.1:
                similar_jobs_with_scores.append({
                    'job': similar_job,
                    'similarity_score': similarity_score
                })

        # Sort by similarity and take top 5
        similar_jobs_with_scores.sort(key=lambda x: x['similarity_score'], reverse=True)
        similar_jobs = [item['job'] for item in similar_jobs_with_scores[:5]]

    except Exception as e:
        # Fallback to simple filtering
        similar_jobs = Job.objects.filter(
            status='Open',
            job_type=job.job_type
        ).exclude(id=job_id)[:5]
    
    # Assess the user's match score for this job
    user_skills = request.user.get_skills_list()
    match_score = 0
    
    if user_skills and job.skills:
        # Simple skill match calculation
        user_skills_set = set([skill.lower().strip() for skill in user_skills])
        job_skills_set = set([skill.lower().strip() for skill in job.skills])
        
        if user_skills_set and job_skills_set:
            # Calculate skill match percentage
            matching_skills = user_skills_set.intersection(job_skills_set)
            match_score = int((len(matching_skills) / len(job_skills_set)) * 100)
    
    context = {
        'job': job,
        'already_applied': already_applied,
        'is_bookmarked': is_bookmarked,
        'similar_jobs': similar_jobs,
        'company_description': company_description,
        'match_score': match_score,
        'matching_skills': user_skills_set.intersection(job_skills_set) if user_skills and job.skills else [],
        'missing_skills': job_skills_set - user_skills_set if user_skills and job.skills else []
    }
    
    return render(request, 'jobs/job_detail.html', context)

@login_required
@require_POST
def apply_for_job(request, job_id):
    """Handle job application submission"""
    job = get_object_or_404(Job, id=job_id, status='Open')
    
    # Check if the user has already applied
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, "You have already applied for this position.")
        return redirect('jobs:job_detail', job_id=job_id)
    
    try:
        # Get application data
        cover_letter = request.POST.get('cover_letter', '')
        resume = request.FILES.get('resume')
        
        # Create the application
        application = Application.objects.create(
            job=job,
            applicant=request.user,
            cover_letter=cover_letter,
            resume=resume,
            status='Applied'
        )

        # Track this application in the recommendation system
        recommender.track_job_application(request.user, job)

        # Send notification to recruiter
        try:
            notify_job_application(request.user, job.posted_by, job.title)
        except Exception as e:
            logger.warning(f"Failed to send notification: {str(e)}")

        messages.success(request, "Your application has been submitted successfully!")
        return redirect('jobs:my_applications')
        
    except Exception as e:
        logger.error(f"Error submitting application for user {request.user.id}: {str(e)}")
        messages.error(request, "There was an error submitting your application. Please try again.")
        return redirect('jobs:job_detail', job_id=job_id)

@login_required
def my_applications(request):
    """Display user's job applications"""
    applications = Application.objects.filter(applicant=request.user).order_by('-applied_at')
    
    context = {
        'applications': applications,
    }
    
    return render(request, 'jobs/my_applications.html', context)

@login_required
def application_detail(request, application_id):
    """Display detailed information about a specific application"""
    application = get_object_or_404(Application, id=application_id, applicant=request.user)
    
    # Get messages related to this application
    messages_thread = application.messages.all().order_by('sent_at')
    
    context = {
        'application': application,
        'messages': messages_thread,
    }
    
    return render(request, 'jobs/application_detail.html', context)

@login_required
@require_POST
def toggle_bookmark(request, job_id):
    """Toggle job bookmark status"""
    job = get_object_or_404(Job, id=job_id)
    
    try:
        # Check if the job is already bookmarked
        bookmark = JobBookmark.objects.filter(job=job, user=request.user)
        
        if bookmark.exists():
            # Remove bookmark
            bookmark.delete()
            return JsonResponse({
                'success': True,
                'bookmarked': False,
                'message': 'Job removed from bookmarks'
            })
        else:
            # Add bookmark
            JobBookmark.objects.create(job=job, user=request.user)
            
            # Track this action for recommendations
            recommender.track_job_bookmark(request.user, job)
            
            return JsonResponse({
                'success': True,
                'bookmarked': True,
                'message': 'Job added to bookmarks'
            })
            
    except Exception as e:
        logger.error(f"Error toggling bookmark for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error updating bookmark status'
        }, status=400)

@login_required
def bookmarked_jobs(request):
    """Display user's bookmarked jobs"""
    bookmarks = JobBookmark.objects.filter(user=request.user).order_by('-bookmarked_at')
    
    context = {
        'bookmarks': bookmarks,
    }
    
    return render(request, 'jobs/bookmarked_jobs.html', context)

@login_required
def recommended_jobs(request):
    """Display personalized job recommendations"""
    try:
        recommended_jobs = recommender.recommend_jobs(request.user, limit=50)
    except Exception as e:
        logger.error(f"Error getting recommendations for user {request.user.id}: {str(e)}")
        recommended_jobs = []
    
    # Get user's applied job IDs for checking
    applied_job_ids = Application.objects.filter(applicant=request.user).values_list('job_id', flat=True)
    
    # Get user's bookmarked job IDs for checking
    bookmarked_job_ids = JobBookmark.objects.filter(user=request.user).values_list('job_id', flat=True)
    
    # Calculate statistics (convert decimal scores to percentages)
    high_match_count = sum(1 for rec in recommended_jobs if rec.get('score', 0) * 100 > 80)
    medium_match_count = sum(1 for rec in recommended_jobs if 60 <= rec.get('score', 0) * 100 <= 80)
    low_match_count = sum(1 for rec in recommended_jobs if rec.get('score', 0) * 100 < 60)
    
    context = {
        'recommended_jobs': recommended_jobs,
        'applied_job_ids': list(applied_job_ids),
        'bookmarked_job_ids': list(bookmarked_job_ids),
        'stats': {
            'total_recommendations': len(recommended_jobs),
            'high_match_count': high_match_count,
            'medium_match_count': medium_match_count,
            'low_match_count': low_match_count,
        }
    }
    
    return render(request, 'jobs/recommended_jobs.html', context)

@login_required
def update_job_preferences(request):
    """Update job preferences for better recommendations"""
    # Get or create current preferences
    try:
        preferences = UserJobPreference.objects.get(user=request.user)
    except UserJobPreference.DoesNotExist:
        preferences = None

    if request.method == 'POST':
        # Use Django form for better validation
        form = UserJobPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            try:
                # Save the form with the current user
                preferences = form.save(commit=False)
                preferences.user = request.user
                preferences.save()

                messages.success(request, "Your job preferences have been updated successfully!")
                return redirect('jobs:recommended_jobs')

            except Exception as e:
                logger.error(f"Error updating job preferences for user {request.user.id}: {str(e)}")
                messages.error(request, "There was an error updating your preferences. Please try again.")
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # GET request - create form with existing data
        form = UserJobPreferenceForm(instance=preferences)

    # Get available job types and industries
    job_types = dict(Job.JOB_TYPE_CHOICES)

    # Get industry choices from the form
    industry_choices = [
        ('Technology', 'Technology'),
        ('Healthcare', 'Healthcare'),
        ('Finance', 'Finance'),
        ('Education', 'Education'),
        ('Marketing', 'Marketing'),
        ('Manufacturing', 'Manufacturing'),
        ('Retail', 'Retail'),
        ('Media', 'Media'),
        ('Construction', 'Construction'),
        ('Transportation', 'Transportation'),
        ('Food Service', 'Food Service'),
    ]

    context = {
        'form': form,
        'preferences': preferences,
        'job_types': job_types,
        'industry_choices': industry_choices,
    }

    return render(request, 'jobs/job_preferences.html', context)

@login_required
def search_jobs(request):
    """Search for jobs based on criteria"""
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    job_type = request.GET.get('job_type', '')
    
    # Base queryset
    jobs = Job.objects.filter(status='Open')
    
    # Apply filters
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) | 
            Q(skills__contains=[query])
        )
    
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    # Get user's applied job IDs
    applied_job_ids = Application.objects.filter(applicant=request.user).values_list('job_id', flat=True)
    
    # Get user's bookmarked job IDs
    bookmarked_job_ids = JobBookmark.objects.filter(user=request.user).values_list('job_id', flat=True)
    
    context = {
        'jobs': jobs,
        'query': query,
        'location': location,
        'job_type': job_type,
        'applied_job_ids': list(applied_job_ids),
        'bookmarked_job_ids': list(bookmarked_job_ids),
        'job_types': dict(Job.JOB_TYPE_CHOICES),
    }
    
    return render(request, 'jobs/search_results.html', context)

@login_required
@require_POST
def send_application_message(request, application_id):
    """Send a message regarding an application"""
    application = get_object_or_404(Application, id=application_id)
    
    # Ensure user is authorized (either the applicant or the recruiter)
    if request.user != application.applicant and request.user != application.job.posted_by:
        messages.error(request, "You are not authorized to send messages for this application.")
        return redirect('jobs:my_applications')
    
    try:
        content = request.POST.get('message_content', '').strip()
        
        if not content:
            messages.error(request, "Message content cannot be empty.")
            return redirect('jobs:application_detail', application_id=application_id)
        
        # Determine recipient
        if request.user == application.applicant:
            recipient = application.job.posted_by
            subject = f"Regarding my application for {application.job.title}"
        else:
            recipient = application.applicant
            subject = f"Regarding your application for {application.job.title}"
        
        # Create message
        from recruiter.models import Message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            application=application,
            subject=subject,
            content=content
        )
        
        messages.success(request, "Your message has been sent successfully!")
        
    except Exception as e:
        logger.error(f"Error sending application message: {str(e)}")
        messages.error(request, "There was an error sending your message. Please try again.")
    
    return redirect('jobs:application_detail', application_id=application_id)

@login_required
def job_analytics(request):
    """Job market analytics and trends"""
    # Only show this to paid members or premium users
    # if not request.user.is_premium:
    #     messages.warning(request, "This feature is available only for premium members.")
    #     return redirect('jobs:job_listings')
    
    # Get top skills in demand
    top_skills = []
    skill_counts = {}
    
    for job in Job.objects.filter(status='Open'):
        for skill in job.skills:
            skill = skill.lower().strip()
            if skill in skill_counts:
                skill_counts[skill] += 1
            else:
                skill_counts[skill] = 1
    
    # Sort skills by count and get top 10
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Get job type distribution
    job_type_counts = Job.objects.filter(status='Open').values('job_type').annotate(
        count=Count('job_type')
    ).order_by('-count')
    
    # Get location distribution
    location_counts = {}
    for job in Job.objects.filter(status='Open'):
        # Simplify location to just city or state
        location_parts = job.location.split(',')
        simple_location = location_parts[0].strip()
        
        if simple_location in location_counts:
            location_counts[simple_location] += 1
        else:
            location_counts[simple_location] = 1
    
    # Sort locations by count and get top 10
    top_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Get user's skill gaps compared to market demand
    user_skills = set([skill.lower().strip() for skill in request.user.get_skills_list()])
    
    # Identify skills in high demand that user doesn't have
    recommended_skills = []
    for skill, count in top_skills:
        if skill not in user_skills and count > 1:
            recommended_skills.append({
                'skill': skill,
                'demand_count': count
            })
    
    context = {
        'total_jobs': Job.objects.filter(status='Open').count(),
        'top_skills': top_skills,
        'job_type_distribution': job_type_counts,
        'top_locations': top_locations,
        'recommended_skills': recommended_skills[:5]
    }
    
    return render(request, 'jobs/job_analytics.html', context)

@login_required
def api_recommended_jobs(request):
    """API endpoint to get recommended jobs"""
    recommended_jobs = recommender.recommend_jobs(request.user)
    
    # Format for API response
    jobs_data = []
    for rec in recommended_jobs:
        job = rec['job']
        jobs_data.append({
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'job_type': job.job_type,
            'score': rec['score'],
            'reason': rec['reason']
        })
    
    return JsonResponse({'recommended_jobs': jobs_data})