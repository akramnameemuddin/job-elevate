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


def _get_match_reason(score_data):
    """Generate a short reason string from score data."""
    pct = score_data.get('skill_match', 0)
    if pct >= 80:
        return 'Excellent skill match'
    elif pct >= 60:
        return 'Strong skill match'
    elif pct >= 40:
        return 'Good skill match'
    elif pct >= 20:
        return 'Partial skill match'
    return 'Potential opportunity'

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
    sort_by = request.GET.get('sort', 'match')  # Default sort by match
    
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
    
    # Compute match scores for ALL jobs using the content-based recommender
    job_match_scores = {}
    try:
        content_rec = recommender.content_recommender
        user_skills = request.user.get_all_skills_list()
        user_experience = request.user.experience
        
        # Load user preferences
        try:
            job_prefs = request.user.job_preferences
            pref_locations = job_prefs.preferred_locations or []
            pref_job_types = job_prefs.preferred_job_types or []
            pref_industries = job_prefs.industry_preferences or []
            pref_min_salary = job_prefs.min_salary_expectation
            pref_remote = job_prefs.remote_preference
        except UserJobPreference.DoesNotExist:
            pref_locations = []
            pref_job_types = []
            pref_industries = []
            pref_min_salary = None
            pref_remote = False
        
        # Compute TF-IDF text similarity for all jobs at once
        text_scores = content_rec.calculate_text_similarity(request.user, jobs)
        
        for job in jobs:
            skill_match = content_rec.calculate_skill_match(user_skills, job.skills)
            text_sim = text_scores.get(job.id, 0.0)
            exp_match = content_rec.calculate_experience_match(user_experience, job.experience)
            loc_match = content_rec.calculate_location_match(pref_locations, job.location)
            jt_match = content_rec.calculate_job_type_match(pref_job_types, job.job_type)
            ind_match = content_rec.calculate_industry_match(
                pref_industries, job.description, job.title, job.company
            )
            sal_match = content_rec.calculate_salary_match(pref_min_salary, job.salary)
            
            pref_score = content_rec.calculate_preference_score(
                exp_match, loc_match, jt_match, ind_match, sal_match
            )
            
            score = (
                content_rec.SKILL_WEIGHT * skill_match +
                content_rec.TEXT_WEIGHT * text_sim +
                content_rec.PREF_WEIGHT * pref_score
            )
            
            if pref_remote and (job.job_type == 'Remote' or 'remote' in job.location.lower()):
                score += 0.05
            
            score = min(score, 1.0)
            job_match_scores[job.id] = {
                'score': score,
                'percentage': int(score * 100),
                'skill_match': int(skill_match * 100),
            }
    except Exception as e:
        logger.error(f"Error computing match scores for user {request.user.id}: {str(e)}")
    
    # Sort jobs by match score if requested (default), else by date
    jobs_list = list(jobs)
    if sort_by == 'match' and job_match_scores:
        jobs_list.sort(key=lambda j: job_match_scores.get(j.id, {}).get('score', 0), reverse=True)
    elif sort_by == 'date':
        jobs_list.sort(key=lambda j: j.created_at, reverse=True)
    elif sort_by == 'salary':
        # Simple salary sort - jobs with salary first
        jobs_list.sort(key=lambda j: j.salary or '', reverse=True)
    
    # Get personalized recommendations — use the SAME content-based scores
    # as the main table so percentages are consistent across the page.
    recommended_jobs = []
    try:
        if job_match_scores:
            # Build recommended list from the content-based scores (already computed)
            for job in jobs_list:
                score_data = job_match_scores.get(job.id, {})
                raw_score = score_data.get('score', 0)
                if raw_score > 0.3:
                    recommended_jobs.append({
                        'job': job,
                        'score': raw_score,
                        'reason': _get_match_reason(score_data),
                    })
            recommended_jobs.sort(key=lambda r: r['score'], reverse=True)
            recommended_jobs = recommended_jobs[:6]
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
    paginator = Paginator(jobs_list, 20)  # Show 20 jobs per page
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
    
    # Check if user has set job preferences
    try:
        user_preferences = request.user.job_preferences
        has_preferences = True
    except UserJobPreference.DoesNotExist:
        user_preferences = None
        has_preferences = False

    # Context for the template
    context = {
        'jobs': jobs_page,
        'job_match_scores': job_match_scores,
        'recommended_jobs': recommended_jobs,
        'bookmarked_jobs': bookmarked_jobs,
        'applied_jobs': applied_jobs,
        'bookmarked_job_ids': bookmarked_job_ids,
        'all_locations': [loc for loc in all_locations if loc],  # Filter out empty locations
        'search_query': search_query,
        'location_filter': location_filter,
        'job_type_filter': job_type_filter,
        'sort_by': sort_by,
        'total_jobs': len(jobs_list),
        'has_filters': bool(search_query or location_filter or job_type_filter),
        'has_preferences': has_preferences,
        'user_preferences': user_preferences,
    }
    
    return render(request, 'jobs/job_listings.html', context)
@login_required
def job_detail(request, job_id):
    """Display detailed job information with comprehensive skill gap analysis"""
    from recruiter.models import JobSkillRequirement
    from assessments.models import UserSkillScore, Skill
    
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

    # Get company description from user profile
    company_description = job.posted_by.company_description if job.posted_by.company_description else None

    # Get similar jobs using improved algorithm
    similar_jobs = []
    try:
        # Get all open jobs except current one
        all_jobs = Job.objects.filter(status='Open').exclude(id=job_id)

        # Calculate similarity scores for better recommendations
        # Extract skill names from job.skills (handle both dict and string formats)
        job_skills_list = []
        if job.skills:
            for skill in job.skills:
                if isinstance(skill, dict):
                    job_skills_list.append(skill.get('name', '').lower())
                else:
                    job_skills_list.append(skill.lower())
        job_skills_set = set(job_skills_list)

        similar_jobs_with_scores = []
        for similar_job in all_jobs:
            # Extract skill names from similar_job.skills
            similar_skills_list = []
            if similar_job.skills:
                for skill in similar_job.skills:
                    if isinstance(skill, dict):
                        similar_skills_list.append(skill.get('name', '').lower())
                    else:
                        similar_skills_list.append(skill.lower())
            similar_skills_set = set(similar_skills_list)

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
    
    # === NEW: COMPREHENSIVE SKILL GAP ANALYSIS ===
    # Get job skill requirements with grades
    skill_requirements = JobSkillRequirement.objects.filter(
        job=job
    ).select_related('skill', 'skill__category').order_by('-criticality', '-required_proficiency')
    
    # Get user's verified skills
    user_skill_profiles = {
        profile.skill_id: profile
        for profile in UserSkillScore.objects.filter(
            user=request.user,
            status='verified'
        ).select_related('skill')
    }
    
    # Get user's claimed but not verified skills
    user_claimed_skills = {
        profile.skill_id: profile
        for profile in UserSkillScore.objects.filter(
            user=request.user,
            status='claimed'
        ).select_related('skill')
    }
    
    # Analyze each skill requirement
    verified_skills = []
    missing_skills = []
    partial_skills = []
    total_skills_required = skill_requirements.count()
    skills_qualified = 0
    overall_match_score = 0
    
    # Also get user's profile skills (from technical_skills CSV field) for broader matching
    user_profile_skills_lower = [s.lower() for s in request.user.get_all_skills_list()]
    
    # If no detailed skill requirements, fall back to basic job.skills
    if total_skills_required == 0 and job.skills:
        from assessments.models import Skill
        # Parse job.skills and create basic analysis
        for skill_data in job.skills:
            # Handle both dict format {'name': 'Python'} and simple string 'Python'
            skill_name = skill_data.get('name') if isinstance(skill_data, dict) else skill_data
            if not skill_name:
                continue
            
            try:
                # Try to find the skill in database (case-insensitive)
                skill = Skill.objects.filter(name__iexact=skill_name).first()
                
                # If skill doesn't exist in database, create placeholder
                if not skill:
                    # Check if user has this skill by name (case-insensitive) via verified profiles OR profile skills
                    user_has_skill = any(
                        profile.skill.name.lower() == skill_name.lower() 
                        for profile in user_skill_profiles.values()
                    ) or skill_name.lower() in user_profile_skills_lower
                    
                    # Create a pseudo-skill object for display
                    class SkillPlaceholder:
                        def __init__(self, name):
                            self.name = name
                            self.id = None
                    
                    skill_analysis = {
                        'skill': SkillPlaceholder(skill_name),
                        'skill_id': None,
                        'name': skill_name,
                        'is_qualified': user_has_skill,
                        'has_profile': user_has_skill,
                        'not_in_db': True
                    }
                    
                    if user_has_skill:
                        verified_skills.append(skill_analysis)
                        skills_qualified += 1
                        overall_match_score += 1
                    else:
                        missing_skills.append(skill_analysis)
                    
                    total_skills_required += 1
                    continue
                
                # Check if user has this skill (case-insensitive by name)
                user_profile = user_skill_profiles.get(skill.id)
                
                # Also check by name in case skill was added with different ID
                if not user_profile:
                    for profile in user_skill_profiles.values():
                        if profile.skill.name.lower() == skill.name.lower():
                            user_profile = profile
                            break
                
                user_level = user_profile.verified_level if user_profile else 0
                
                # If no verified level, check if user has the skill in their profile
                has_profile_skill = skill.name.lower() in user_profile_skills_lower
                if user_level == 0 and has_profile_skill:
                    user_level = 3.0  # Profile-claimed skill gets a baseline level
                
                # Create basic skill analysis (no detailed requirements)
                skill_analysis = {
                    'skill': skill,
                    'skill_id': skill.id,
                    'name': skill.name,
                    'is_qualified': user_level > 0,
                    'has_profile': user_level > 0,
                    'not_in_db': False
                }
                
                if user_level > 0:
                    verified_skills.append(skill_analysis)
                    skills_qualified += 1
                    overall_match_score += 1
                else:
                    missing_skills.append(skill_analysis)
                
                total_skills_required += 1
            except Exception as e:
                logger.error(f"Error processing skill {skill_name}: {e}", exc_info=True)
                continue
    
    # If we have JobSkillRequirement records, do detailed analysis
    # Qualification threshold: user is "qualified" if they have >= 70% of required proficiency
    QUALIFICATION_THRESHOLD = 0.70
    
    for req in skill_requirements:
        user_profile = user_skill_profiles.get(req.skill_id)
        user_level = user_profile.verified_level if user_profile else 0
        is_claimed = req.skill_id in user_claimed_skills
        
        # Also check profile skills for broader matching
        has_profile_skill = req.skill.name.lower() in user_profile_skills_lower
        if user_level == 0 and has_profile_skill:
            user_level = 3.0
        
        # Determine qualification status using 70% threshold
        threshold_level = req.required_proficiency * QUALIFICATION_THRESHOLD
        is_qualified = user_level >= threshold_level and user_level > 0
        
        skill_analysis = {
            'skill': req.skill,
            'skill_id': req.skill_id,
            'name': req.skill.name,
            'is_mandatory': req.is_mandatory,
            'skill_type': req.skill_type,
            'weight': req.weight,
            'is_qualified': is_qualified,
            'has_profile': user_profile is not None or has_profile_skill,
            'is_claimed': is_claimed,
            'not_in_db': False,
        }
        
        # Categorize skills
        if is_qualified:
            verified_skills.append(skill_analysis)
            skills_qualified += 1
            overall_match_score += req.weight
        elif user_level > 0:
            partial_skills.append(skill_analysis)
            overall_match_score += (user_level / req.required_proficiency) * req.weight if req.required_proficiency > 0 else 0
        else:
            missing_skills.append(skill_analysis)
    
    # Calculate overall match percentage
    total_weight = sum(req.weight for req in skill_requirements)
    if total_weight > 0:
        match_percentage = int((overall_match_score / total_weight * 100))
    elif total_skills_required > 0:
        match_percentage = int((overall_match_score / total_skills_required * 100))
    else:
        match_percentage = 0
    
    # Check eligibility - allow apply for all users (no mandatory lock)
    can_apply = True
    mandatory_skills_met = True
    
    # Recommend assessment if skills are missing
    recommended_assessments = []
    if missing_skills or partial_skills:
        from assessments.models import Assessment
        missing_skill_ids = [s.get('skill_id', s['skill'].id) for s in missing_skills] + [s.get('skill_id', s['skill'].id) for s in partial_skills]
        recommended_assessments = Assessment.objects.filter(
            skill_id__in=missing_skill_ids,
            is_active=True
        ).select_related('skill')[:5]
    
    # Get user's site-built resumes for the apply modal
    from resume_builder.models import Resume, TailoredResume
    user_resumes = Resume.objects.filter(user=request.user).order_by('-updated_at')
    
    # Get AI-tailored resumes (applied/reviewed status) for this job or others
    tailored_resumes = TailoredResume.objects.filter(
        user=request.user,
        status__in=['applied', 'reviewed']
    ).select_related('job').order_by('-updated_at')
    
    # Create simple skill name lists for sidebar display
    matching_skills_simple = [s['skill'].name for s in verified_skills]
    
    # Combine missing and partial skills for "Skills to Develop"
    skills_to_develop = []
    for s in partial_skills:
        skills_to_develop.append({
            'name': s['skill'].name,
            'status': 'needs_improvement',
            'skill_id': s.get('skill_id'),
            'not_in_db': s.get('not_in_db', False)
        })
    for s in missing_skills:
        skills_to_develop.append({
            'name': s.get('name', s['skill'].name),
            'status': 'missing',
            'skill_id': s.get('skill_id'),
            'not_in_db': s.get('not_in_db', False)
        })
    
    context = {
        'job': job,
        'already_applied': already_applied,
        'is_bookmarked': is_bookmarked,
        'similar_jobs': similar_jobs,
        'company_description': company_description,
        'match_score': match_percentage,
        
        # New skill gap analysis (detailed dictionaries for main section)
        'skill_requirements': skill_requirements,
        'verified_skills': verified_skills,
        'missing_skills': missing_skills,
        'partial_skills': partial_skills,
        
        # Simple skill name lists for sidebar
        'matching_skills': matching_skills_simple,
        'skills_to_develop': skills_to_develop,
        'missing_skills_simple': [s['name'] for s in skills_to_develop],  # For backward compatibility
        
        'total_skills_required': total_skills_required,
        'skills_qualified': skills_qualified,
        'can_apply': can_apply,
        'mandatory_skills_met': mandatory_skills_met,
        'recommended_assessments': recommended_assessments,
        'user_resumes': user_resumes,
        'tailored_resumes': tailored_resumes,
    }
    
    return render(request, 'jobs/job_detail.html', context)


@login_required
def claim_skill_from_job(request, job_id, skill_id):
    """Claim a skill from job detail page and redirect to assessment"""
    from assessments.models import Skill, UserSkillScore
    
    skill = get_object_or_404(Skill, id=skill_id, is_active=True)
    
    # Create or get user skill score
    profile, created = UserSkillScore.objects.get_or_create(
        user=request.user,
        skill=skill,
        defaults={
            'self_rated_level': 0,
            'verified_level': 0,
            'status': 'claimed'
        }
    )
    
    if created:
        messages.success(request, f"Skill '{skill.name}' added to your profile. Take the assessment to verify it!")
    else:
        messages.info(request, f"Skill '{skill.name}' already in your profile.")
    
    # Redirect to start assessment from job context
    return redirect('assessments:start_assessment_from_job', job_id=job_id, skill_id=skill_id)

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
        resume_id = request.POST.get('resume_id')
        tailored_resume_id = request.POST.get('tailored_resume_id')
        
        # Get the selected resume's PDF file
        resume_file = None
        selected_resume_title = None
        
        if tailored_resume_id:
            # User selected an AI-tailored resume
            from resume_builder.models import TailoredResume
            try:
                tailored = TailoredResume.objects.get(id=tailored_resume_id, user=request.user)
                selected_resume_title = f"AI Tailored for {tailored.job.title}"
                # Generate tailored PDF using the ReportLab engine
                try:
                    from resume_builder.views import _build_tailored_context, _get_resume_template
                    from resume_builder.pdf_generator import generate_resume_pdf
                    from django.core.files.base import ContentFile

                    ctx = _build_tailored_context(tailored, request.user)
                    user_profile = ctx.get('user_profile', request.user)

                    # Get the resume object for colour/toggle info
                    resume_obj = tailored.base_resume if tailored.base_resume else None

                    pdf_bytes = generate_resume_pdf(user_profile, resume=resume_obj, context=ctx)
                    if pdf_bytes:
                        filename = f"{request.user.full_name.replace(' ', '_')}_Tailored.pdf"
                        resume_file = ContentFile(pdf_bytes, name=filename)
                except Exception as pdf_err:
                    logger.warning(f"Failed to generate tailored PDF: {pdf_err}")
                    # Fall back to base resume PDF if available
                    if tailored.base_resume and tailored.base_resume.pdf_file:
                        resume_file = tailored.base_resume.pdf_file

                tailored.status = 'submitted'
                tailored.save()
            except TailoredResume.DoesNotExist:
                pass
        elif resume_id:
            from resume_builder.models import Resume
            try:
                site_resume = Resume.objects.get(id=resume_id, user=request.user)
                selected_resume_title = site_resume.title
                if site_resume.pdf_file:
                    resume_file = site_resume.pdf_file
            except Resume.DoesNotExist:
                pass
        
        # Create the application
        application = Application.objects.create(
            job=job,
            applicant=request.user,
            cover_letter=cover_letter,
            resume=resume_file,
            status='Applied'
        )

        # Track this application in the recommendation system
        try:
            recommender.track_job_application(request.user, job)
        except Exception as track_err:
            # Log but don't fail the application
            logger.warning(f"Failed to track application in recommender: {str(track_err)}")

        # Send notification to recruiter
        try:
            notify_job_application(request.user, job.posted_by, job.title)
        except Exception as e:
            logger.warning(f"Failed to send notification: {str(e)}")

        messages.success(request, "Your application has been submitted successfully!")
        return redirect('jobs:my_applications')
        
    except Exception as e:
        logger.error(f"Error submitting application for user {request.user.id}: {str(e)}", exc_info=True)
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
    """Display personalized job recommendations using content-based scoring."""
    try:
        # Use the SAME content-based recommender as the main listings page
        content_rec = recommender.content_recommender
        raw_recommendations = content_rec.recommend_jobs(request.user, limit=50)
    except Exception as e:
        logger.error(f"Error getting recommendations for user {request.user.id}: {str(e)}")
        raw_recommendations = []
    
    # Convert decimal scores (0-1) to percentage values for display
    recommended_jobs = []
    for rec in raw_recommendations:
        rec['score'] = int(rec.get('score', 0) * 100)
        recommended_jobs.append(rec)
    
    # Get user's applied job IDs for checking
    applied_job_ids = Application.objects.filter(applicant=request.user).values_list('job_id', flat=True)
    
    # Get user's bookmarked job IDs for checking
    bookmarked_job_ids = JobBookmark.objects.filter(user=request.user).values_list('job_id', flat=True)
    
    # Calculate statistics (scores are now in percentage form)
    high_match_count = sum(1 for rec in recommended_jobs if rec.get('score', 0) > 80)
    medium_match_count = sum(1 for rec in recommended_jobs if 60 <= rec.get('score', 0) <= 80)
    low_match_count = sum(1 for rec in recommended_jobs if rec.get('score', 0) < 60)
    
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
                
                # Sync preferred location to User model for recruiter visibility
                if preferences.preferred_locations:
                    request.user.preferred_location = preferences.preferred_locations[0]
                else:
                    request.user.preferred_location = ''
                request.user.save(update_fields=['preferred_location'])

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
        ('Consulting', 'Consulting'),
        ('Government', 'Government'),
        ('E-commerce', 'E-commerce'),
        ('Telecommunications', 'Telecommunications'),
        ('Energy', 'Energy'),
    ]
    
    currency_choices = UserJobPreference.CURRENCY_CHOICES
    salary_period_choices = UserJobPreference.SALARY_PERIOD_CHOICES
    
    experience_level_choices = [
        ('fresher', 'Fresher (0-1 years)'),
        ('junior', 'Junior (1-3 years)'),
        ('mid', 'Mid Level (3-5 years)'),
        ('senior', 'Senior (5-8 years)'),
        ('lead', 'Lead (8-12 years)'),
        ('principal', 'Principal (12+ years)'),
    ]

    context = {
        'form': form,
        'preferences': preferences,
        'job_types': job_types,
        'industry_choices': industry_choices,
        'currency_choices': currency_choices,
        'salary_period_choices': salary_period_choices,
        'experience_level_choices': experience_level_choices,
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
    open_jobs = Job.objects.filter(status='Open')

    # ── Top skills in demand ──
    skill_counts = {}
    for job in open_jobs:
        for skill in job.skills:
            s = skill.lower().strip()
            skill_counts[s] = skill_counts.get(s, 0) + 1
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # ── Job type distribution ──
    job_type_counts = open_jobs.values('job_type').annotate(
        count=Count('job_type')
    ).order_by('-count')

    # ── Location distribution ──
    location_counts = {}
    for job in open_jobs:
        loc = job.location.split(',')[0].strip()
        location_counts[loc] = location_counts.get(loc, 0) + 1
    top_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # ── Experience level distribution ──
    exp_buckets = {'Entry (0-1y)': 0, 'Junior (1-3y)': 0, 'Mid (3-5y)': 0, 'Senior (5+y)': 0}
    for job in open_jobs:
        exp = job.experience or 0
        if exp <= 1:
            exp_buckets['Entry (0-1y)'] += 1
        elif exp <= 3:
            exp_buckets['Junior (1-3y)'] += 1
        elif exp <= 5:
            exp_buckets['Mid (3-5y)'] += 1
        else:
            exp_buckets['Senior (5+y)'] += 1
    experience_distribution = [{'level': k, 'count': v} for k, v in exp_buckets.items() if v > 0]

    # ── Salary insights ──
    salary_jobs = open_jobs.exclude(salary__isnull=True).exclude(salary='')
    salary_data = []
    for job in salary_jobs[:20]:
        salary_data.append({'title': job.title, 'salary': job.salary, 'company': job.company})

    # ── Skills the user should learn ──
    user_skills = set(s.lower().strip() for s in request.user.get_skills_list())
    recommended_skills = []
    for skill, count in top_skills:
        if skill not in user_skills and count > 1:
            recommended_skills.append({'skill': skill, 'demand_count': count})

    # ── Skill overlap score ──
    if top_skills:
        market_skills = set(s for s, _ in top_skills)
        overlap = len(user_skills & market_skills)
        skill_overlap_pct = round(overlap / len(market_skills) * 100)
    else:
        skill_overlap_pct = 0

    context = {
        'total_jobs': open_jobs.count(),
        'top_skills': top_skills,
        'job_type_distribution': job_type_counts,
        'top_locations': top_locations,
        'recommended_skills': recommended_skills[:5],
        'experience_distribution': experience_distribution,
        'salary_data': salary_data,
        'skill_overlap_pct': skill_overlap_pct,
        'user_skill_count': len(user_skills),
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