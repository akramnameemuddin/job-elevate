from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User, RecruiterProfile
from recruiter.models import Job  # Import Job model
from jobs.recommendation_engine import HybridRecommender  # Import recommendation engine
import logging
import json

@login_required
def profile(request):
    user = request.user

    if request.method == 'POST':
        post = request.POST

        # Basic Info
        user.full_name = post.get('full_name', '').strip()
        user.phone_number = post.get('phone_number', '').strip()
        user.user_type = post.get('user_type', user.user_type)
        user.objective = post.get('objective', '').strip()
        user.linkedin_profile = post.get('linkedin_profile', '').strip()
        user.github_profile = post.get('github_profile', '').strip()
        user.portfolio_website = post.get('portfolio_website', '').strip()
        
        # Education & Skills
        user.university = post.get('university', '').strip()
        user.degree = post.get('degree', '').strip()
        user.graduation_year = post.get('graduation_year') or None
        user.cgpa = post.get('cgpa') or None
        user.technical_skills = post.get('technical_skills', '').strip()
        user.soft_skills = post.get('soft_skills', '').strip()

        # Experience - Current Job
        user.job_title = post.get('job_title', '').strip()
        user.organization = post.get('organization', '').strip()
        user.experience = post.get('experience') or None
        user.industry = post.get('industry', '').strip()
        user.achievements = post.get('achievements', '').strip()
        user.work_experience_description = post.get('work_experience_description', '').strip()

        
        # Handle JSON formatted data for structured fields
        
        # Process work experience entries
        work_experience_entries = []
        work_exp_count = int(post.get('work_experience_count', 0))
        for i in range(work_exp_count):
            if post.get(f'work_exp_title_{i}'):
                entry = {
                    'title': post.get(f'work_exp_title_{i}', '').strip(),
                    'company': post.get(f'work_exp_company_{i}', '').strip(),
                    'location': post.get(f'work_exp_location_{i}', '').strip(),
                    'start_date': post.get(f'work_exp_start_date_{i}', '').strip(),
                    'end_date': post.get(f'work_exp_end_date_{i}', '').strip() or "Present",
                    'is_current': post.get(f'work_exp_is_current_{i}') == 'on',
                    'description': post.get(f'work_exp_description_{i}', '').strip(),
                    'skills': post.get(f'work_exp_skills_{i}', '').strip(),
                }
                work_experience_entries.append(entry)
        
        if work_experience_entries:
            user.work_experience = json.dumps(work_experience_entries)
        
        # Process internship entries
        internship_entries = []
        intern_count = int(post.get('internship_count', 0))
        for i in range(intern_count):
            if post.get(f'intern_title_{i}'):
                entry = {
                    'title': post.get(f'intern_title_{i}', '').strip(),
                    'company': post.get(f'intern_company_{i}', '').strip(),
                    'location': post.get(f'intern_location_{i}', '').strip(),
                    'start_date': post.get(f'intern_start_date_{i}', '').strip(),
                    'end_date': post.get(f'intern_end_date_{i}', '').strip() or "Present",
                    'is_current': post.get(f'intern_is_current_{i}') == 'on',
                    'description': post.get(f'intern_description_{i}', '').strip(),
                    'skills': post.get(f'intern_skills_{i}', '').strip(),
                }
                internship_entries.append(entry)
        
        user.internships = json.dumps(internship_entries)
        
        # Process certification entries
        certification_entries = []
        cert_count = int(post.get('certification_count', 0))
        for i in range(cert_count):
            if post.get(f'cert_name_{i}'):
                entry = {
                    'name': post.get(f'cert_name_{i}', '').strip(),
                    'organization': post.get(f'cert_organization_{i}', '').strip(),
                    'issue_date': post.get(f'cert_issue_date_{i}', '').strip(),
                    'expiration_date': post.get(f'cert_expiration_date_{i}', '').strip(),
                    'credential_id': post.get(f'cert_credential_id_{i}', '').strip(),
                    'credential_url': post.get(f'cert_credential_url_{i}', '').strip(),
                    'skills': post.get(f'cert_skills_{i}', '').strip(),
                    'media': post.get(f'cert_media_{i}', '').strip(),
                }
                certification_entries.append(entry)
        
        user.certifications = json.dumps(certification_entries)
            
        # Process project entries
        project_entries = []
        project_count = int(post.get('project_count', 0))
        for i in range(project_count):
            if post.get(f'project_title_{i}'):
                entry = {
                    'title': post.get(f'project_title_{i}', '').strip(),
                    'description': post.get(f'project_description_{i}', '').strip(), 
                    'start_date': post.get(f'project_start_date_{i}', '').strip(),
                    'end_date': post.get(f'project_end_date_{i}', '').strip(),
                    'skills': post.get(f'project_skills_{i}', '').strip(),
                    'url': post.get(f'project_url_{i}', '').strip(),
                    'github_url': post.get(f'project_github_url_{i}', '').strip(),
                }
                project_entries.append(entry)
        
        user.projects = json.dumps(project_entries)

        # Handle extracurricular activities
        user.extracurricular_activities = post.get('extracurricular_activities', '').strip()
        
        logger = logging.getLogger(__name__)

        # Profile Photo
        if request.FILES.get('profile_photo'):
            logger.info("Uploaded image: %s", request.FILES['profile_photo'].name)
            user.profile_photo = request.FILES['profile_photo']

        user.save()

        # Recruiter profile (only if recruiter)
        if user.user_type == 'recruiter':
            recruiter_profile, created = RecruiterProfile.objects.get_or_create(user=user)
            recruiter_profile.company_name = post.get('company_name', '').strip()
            recruiter_profile.company_website = post.get('company_website', '').strip()
            recruiter_profile.company_description = post.get('company_description', '').strip()
            recruiter_profile.save()

        messages.success(request, "Profile updated successfully!")

    # Compute initials from full name
    full_name = user.full_name.strip() if user.full_name else ""
    name_parts = full_name.split()
    if len(name_parts) >= 2:
        initials = name_parts[0][0].upper() + name_parts[-1][0].upper()
    elif len(name_parts) == 1:
        initials = name_parts[0][0].upper()
    else:
        initials = "US"
    
    # Prepare data for template
    profile_percent = user.profile_completion()
    job_match_count = user.get_job_matches_count()

    # Get structured data from JSON fields
    work_experiences = user.get_work_experience()
    internships_raw = user.get_internships()
    internships = []
    for intern in internships_raw:
        skills_list = [skill.strip() for skill in intern.get('skills', '').split(',') if skill.strip()]
        intern['skills_list'] = skills_list
        internships.append(intern)
 
    # Process Projects
    projects_raw = user.get_projects()
    projects = []
    for proj in projects_raw:
        skills_list = [skill.strip() for skill in proj.get('skills', '').split(',') if skill.strip()]
        proj['skills_list'] = skills_list
        projects.append(proj)

    # Process Certifications
    certs_raw = user.get_certifications()
    certifications = []
    for cert in certs_raw:
        skills_list = [skill.strip() for skill in cert.get('skills', '').split(',') if skill.strip()]
        cert['skills_list'] = skills_list
        certifications.append(cert)

    
    context = {
        'user': user,
        'user_initials': initials,
        'profile_percent': profile_percent,
        'job_match_count': job_match_count,
        'work_experiences': work_experiences,
        'internships': internships,
        'certifications': certifications,
        'projects': projects,
    }
    context['show_internships'] = user.user_type == 'student'
    context['show_experience'] = user.user_type == 'professional'
    # Render template based on user type
    if user.user_type in ['student', 'professional']:
        return render(request, 'dashboard/profile.html', context)
    elif user.user_type == 'recruiter':
        return render(request, 'dashboard/recruiter_profile.html', context)
    
    return redirect('accounts:login')


@login_required
def dashboard(request):
    user = request.user

    # Compute initials from full name
    full_name = user.full_name.strip() if user.full_name else ""
    name_parts = full_name.split()
    if len(name_parts) >= 2:
        initials = name_parts[0][0].upper() + name_parts[-1][0].upper()
    elif len(name_parts) == 1:
        initials = name_parts[0][0].upper()
    else:
        initials = "US"

    # Calculate job matches using the user model method
    job_match_count = user.get_job_matches_count()
    
    # Calculate profile completion percentage
    profile_completion = user.profile_completion()

    context = {
        'user': user,
        'user_initials': initials,
        'job_match_count': job_match_count,
        'profile_completion': profile_completion,
        'courses_completed': 7,  # Static for now as mentioned
        'network_growth': 28,    # Static for now as mentioned
    }

    # Only allow access for students and professionals
    if user.user_type in ['student', 'professional']:
        return render(request, 'dashboard/base.html', context)
    elif user.user_type == 'recruiter':
        # Redirect to recruiter dashboard
        return redirect('recruiter/')

    # For others (including recruiters), show 403 or custom error
    return render(request, 'accounts/access_denied.html', status=403)

# Add a new view function for dashboard home specifically
@login_required
def home(request):
    user = request.user

    # Compute initials from full name
    full_name = user.full_name.strip() if user.full_name else ""
    name_parts = full_name.split()
    if len(name_parts) >= 2:
        initials = name_parts[0][0].upper() + name_parts[-1][0].upper()
    elif len(name_parts) == 1:
        initials = name_parts[0][0].upper()
    else:
        initials = "US"

    # Calculate job matches using the user model method
    job_match_count = user.get_job_matches_count()
    
    # Calculate profile completion percentage
    profile_completion = user.profile_completion()

    context = {
        'user': user,
        'user_initials': initials,
        'job_match_count': job_match_count,
        'profile_completion': profile_completion,
        'courses_completed': 7,  # Static for now as mentioned
        'network_growth': 28,    # Static for now as mentioned
    }

    # Only allow access for students and professionals
    if user.user_type in ['student', 'professional']:
        return render(request, 'dashboard/base.html', context)
    elif user.user_type == 'recruiter':
        # Redirect to recruiter dashboard
        return redirect('recruiter/')

    # For others (including recruiters), show 403 or custom error
    return render(request, 'accounts/access_denied.html', status=403)