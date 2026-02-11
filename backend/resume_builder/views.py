from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
import json
import os
from io import BytesIO

from accounts.models import User
from recruiter.models import Job
from .models import ResumeTemplate, Resume, TailoredResume
from .pdf_generator import generate_resume_pdf
from django.template import Template, Context


@login_required
def resume_dashboard(request):
    """Show all user resumes, template options, and tailored resumes"""
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

    # Get resumes and templates
    user_resumes = Resume.objects.filter(user=user)
    resume_templates = ResumeTemplate.objects.filter(is_active=True)
    tailored_resumes = TailoredResume.objects.filter(user=user).select_related('job', 'base_resume')[:6]

    # Profile completeness for the wizard prompt
    profile_fields = [
        user.full_name, user.email, user.phone_number, user.objective,
        user.university, user.degree, user.technical_skills,
    ]
    has_projects = bool(user.get_projects())
    has_experience = bool(user.get_work_experience() if hasattr(user, 'get_work_experience') else [])
    filled = sum(1 for f in profile_fields if f) + int(has_projects) + int(has_experience)
    profile_completeness = min(int((filled / 9) * 100), 100)

    context = {
        'user_resumes': user_resumes,
        'resume_templates': resume_templates,
        'tailored_resumes': tailored_resumes,
        'user_initials': initials,
        'profile_completeness': profile_completeness,
        'total_resumes': user_resumes.count(),
        'total_downloads': sum(r.download_count for r in user_resumes),
    }

    return render(request, 'resume_builder/dashboard.html', context)

@login_required
def create_resume(request):
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
    else:
        template_id = request.GET.get('template_id')  # NEW
    
    if not template_id:
        messages.error(request, "Please select a template")
        return redirect('resume_builder:dashboard')

    template = get_object_or_404(ResumeTemplate, id=template_id)
    title = f"Resume {timezone.now().strftime('%b %d, %Y')}"

    resume = Resume.objects.create(
        user=request.user,
        template=template,
        title=title
    )
    messages.success(request, "Resume created successfully! You can now customize it.")
    return redirect('resume_builder:edit_resume', resume_id=resume.id)


@login_required
def edit_resume(request, resume_id):
    """Edit an existing resume"""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    if request.method == 'POST':
        # Update resume customization options
        resume.title = request.POST.get('title', resume.title)
        resume.primary_color = request.POST.get('primary_color', resume.primary_color)
        resume.secondary_color = request.POST.get('secondary_color', resume.secondary_color)
        resume.font_family = request.POST.get('font_family', resume.font_family)
        
        # Update section visibility toggles
        resume.show_contact = 'show_contact' in request.POST
        resume.show_links = 'show_links' in request.POST
        resume.show_objective = 'show_objective' in request.POST
        resume.show_education = 'show_education' in request.POST
        resume.show_skills = 'show_skills' in request.POST
        resume.show_experience = 'show_experience' in request.POST
        resume.show_projects = 'show_projects' in request.POST
        resume.show_certifications = 'show_certifications' in request.POST
        resume.show_achievements = 'show_achievements' in request.POST
        resume.show_extracurricular = 'show_extracurricular' in request.POST
        
        resume.save()
        messages.success(request, "Resume updated successfully!")
        
        # If "Preview" button was clicked
        if 'preview' in request.POST:
            return redirect('resume_builder:preview_resume', resume_id=resume.id)
            
        # If "Save and Download" button was clicked
        if 'download' in request.POST:
            return redirect('resume_builder:download_resume', resume_id=resume.id)
    
    # User's profile data
    user = request.user
    
    # Additional template data
    context = {
        'resume': resume,
        'user_profile': user,
        'projects': user.get_projects(),
        'internships': user.get_internships(),
        'work_experience': user.get_work_experience(),
        'certifications': user.get_certifications(),
        'technical_skills': user.get_skills_list(),
    }
    
    return render(request, 'resume_builder/edit.html', context)

@login_required
def preview_resume(request, resume_id):
    """Preview the resume"""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    user = request.user

    # Preprocess achievements into a cleaned list
    if hasattr(user, 'achievements') and user.achievements:
        achievements_list = [
            achievement.strip() for achievement in user.achievements.split('\n') if achievement.strip()
        ]
    else:
        achievements_list = []

    context = {
        'resume': resume,
        'user_profile': user,
        'projects': user.get_projects(),
        'internships': user.get_internships(),
        'work_experience': user.get_work_experience(),
        'certifications': user.get_certifications(),
        'technical_skills': user.get_skills_list(),
        'achievements_list': achievements_list,  # include this
        'is_preview': True
    }

    # Render using the template stored in DB
    html_string = Template(resume.template.html_structure).render(Context(context))

    # Render CSS template (contains Django template tags for colours)
    try:
        css_string = Template(resume.template.css_structure).render(Context(context))
    except Exception:
        css_string = ''

    # Wrap in full HTML document with CSS so each template looks distinct
    full_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>{css_string}</style>
</head><body>{html_string}</body></html>"""

    return HttpResponse(full_html)

@login_required
def download_resume(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    user = request.user

    try:
        # Prepare context data for the PDF generator
        projects = user.get_projects()
        for project in projects:
            if project.get('technologies'):
                project['tech_list'] = [tech.strip() for tech in project['technologies'].split(',')]
            else:
                project['tech_list'] = []

        internships = user.get_internships()
        work_experience = user.get_work_experience()

        achievements_list = []
        if hasattr(user, 'achievements') and user.achievements:
            achievements_list = [a.strip() for a in user.achievements.split('\n') if a.strip()]

        extracurricular = user.extracurricular_activities if user.extracurricular_activities else ''

        context = {
            'user_profile': user,
            'projects': projects,
            'internships': internships,
            'work_experience': work_experience,
            'certifications': user.get_certifications(),
            'technical_skills': user.get_skills_list(),
            'achievements_list': achievements_list,
            'extracurricular_html': extracurricular,
        }

        # Generate PDF using the ReportLab-based engine
        pdf_content = generate_resume_pdf(user, resume=resume, context=context)

        # Update resume metadata
        resume.download_count += 1
        resume.last_downloaded = timezone.now()
        resume.save()

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{user.full_name.replace(" ", "_")}_Resume.pdf"'
        response['Content-Length'] = len(pdf_content)
        return response

    except Exception as e:
        import logging
        logging.error(f'Resume download error: {str(e)}')
        return HttpResponse(
            f'An error occurred while generating your resume: {str(e)}',
            status=500,
            content_type='text/plain'
        )

@login_required
def delete_resume(request, resume_id):
    """Delete a resume"""
    # Always check if resume exists and belongs to user, regardless of method
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)

    if request.method == 'POST':
        try:
            resume_title = resume.title
            resume.delete()
            messages.success(request, f"Resume '{resume_title}' deleted successfully!")
        except Exception as e:
            messages.error(request, "Failed to delete resume. Please try again.")
    else:
        messages.error(request, "Invalid request method.")

    return redirect('resume_builder:resume_builder')

@login_required
def change_template(request, resume_id):
    """Change the template of an existing resume"""
    if request.method == 'POST':
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        template_id = request.POST.get('template_id')
        
        if template_id:
            template = get_object_or_404(ResumeTemplate, id=template_id)
            resume.template = template
            resume.save()
            messages.success(request, "Resume template changed successfully!")
        
    return redirect('resume_builder:edit_resume', resume_id=resume.id)


@login_required
def resume_analyzer(request, job_id):
    """Compare user profile/resume against a specific job's requirements."""
    job = get_object_or_404(Job, id=job_id)
    user = request.user

    # User skills (normalised to lowercase for matching)
    user_skills_raw = user.get_skills_list() if hasattr(user, 'get_skills_list') else []
    user_skills_lower = {s.lower().strip() for s in user_skills_raw}

    # Job skills – may be list of dicts or list of strings
    job_skills_raw = job.skills or []
    job_skill_names = []
    for item in job_skills_raw:
        if isinstance(item, dict):
            job_skill_names.append(item.get('name', item.get('skill', '')))
        else:
            job_skill_names.append(str(item))
    job_skill_names = [s.strip() for s in job_skill_names if s.strip()]

    matched = [s for s in job_skill_names if s.lower() in user_skills_lower]
    missing = [s for s in job_skill_names if s.lower() not in user_skills_lower]
    total_job = len(job_skill_names)
    match_score = int((len(matched) / total_job) * 100) if total_job else 0

    # Profile strength
    profile_fields = [
        user.full_name, user.email, user.phone_number, user.objective,
        user.university, user.degree, user.technical_skills,
    ]
    has_projects = bool(user.get_projects())
    has_experience = bool(user.get_work_experience() if hasattr(user, 'get_work_experience') else [])
    filled = sum(1 for f in profile_fields if f) + int(has_projects) + int(has_experience)
    profile_strength = min(int((filled / 9) * 100), 100)

    # Initials
    name_parts = (user.full_name or '').split()
    if len(name_parts) >= 2:
        initials = name_parts[0][0].upper() + name_parts[-1][0].upper()
    elif len(name_parts) == 1:
        initials = name_parts[0][0].upper()
    else:
        initials = 'U'

    has_resume = Resume.objects.filter(user=user).exists()

    context = {
        'job': job,
        'matched_skills': matched,
        'missing_skills': missing,
        'match_score': match_score,
        'total_job_skills': total_job,
        'user': user,
        'user_initials': initials,
        'user_skills_count': len(user_skills_raw),
        'experience_count': len(user.get_work_experience() if hasattr(user, 'get_work_experience') else []),
        'projects_count': len(user.get_projects()),
        'profile_strength': profile_strength,
        'has_resume': has_resume,
    }
    return render(request, 'resume_builder/analyzer.html', context)


# ---------------------------------------------------------------------------
# Tailored resume preview & download
# ---------------------------------------------------------------------------

def _build_tailored_context(tailored, user):
    """
    Build rendering context for a TailoredResume.
    Uses tailored fields when available, falls back to user profile data.
    """
    # Skills: use tailored if available, else user profile
    skills = tailored.tailored_skills or user.get_skills_list()

    # Objective: use tailored if available
    objective = tailored.tailored_objective or (user.objective or '')

    # Experience & projects: use tailored snapshots (which come from user profile + AI edits)
    experience = tailored.tailored_experience or (user.get_work_experience() if hasattr(user, 'get_work_experience') else [])
    projects = tailored.tailored_projects or (user.get_projects() if hasattr(user, 'get_projects') else [])

    # Process data for rendering
    for project in projects:
        if project.get('technologies'):
            project['tech_list'] = [t.strip() for t in project['technologies'].split(',')]
        else:
            project['tech_list'] = []
        if project.get('description'):
            project['description'] = project['description'].replace('\n', '<br>')

    internships = user.get_internships() if hasattr(user, 'get_internships') else []
    for internship in internships:
        if internship.get('description'):
            internship['description'] = internship['description'].replace('\n', '<br>')

    for job in experience:
        if job.get('description'):
            job['description'] = job['description'].replace('\n', '<br>')

    linkedin_link = f'<a href="{user.linkedin_profile}" target="_blank">{user.linkedin_profile}</a>' if user.linkedin_profile else ''
    github_link = f'<a href="{user.github_profile}" target="_blank">{user.github_profile}</a>' if user.github_profile else ''
    website_link = f'<a href="{user.portfolio_website}" target="_blank">{user.portfolio_website}</a>' if user.portfolio_website else ''

    skill_rows = [skills[i:i+3] for i in range(0, len(skills), 3)]

    achievements_list = []
    if hasattr(user, 'achievements') and user.achievements:
        achievements_list = [a.strip() for a in user.achievements.split('\n') if a.strip()]

    extracurricular_html = user.extracurricular_activities.replace('\n', '<br>') if user.extracurricular_activities else ''

    # Create a pseudo-resume object for templates that reference resume.show_*
    class ResumeProxy:
        """Proxy that enables all sections for tailored resume rendering."""
        show_contact = True
        show_links = True
        show_objective = True
        show_education = True
        show_skills = True
        show_experience = True
        show_projects = True
        show_certifications = True
        show_achievements = True
        show_extracurricular = True
        primary_color = '#4f46e5'
        secondary_color = '#6b7280'
        font_family = 'Roboto, sans-serif'

        def __init__(self, base_resume=None):
            if base_resume:
                self.show_contact = base_resume.show_contact
                self.show_links = base_resume.show_links
                self.show_objective = base_resume.show_objective
                self.show_education = base_resume.show_education
                self.show_skills = base_resume.show_skills
                self.show_experience = base_resume.show_experience
                self.show_projects = base_resume.show_projects
                self.show_certifications = base_resume.show_certifications
                self.show_achievements = base_resume.show_achievements
                self.show_extracurricular = base_resume.show_extracurricular
                self.primary_color = base_resume.primary_color
                self.secondary_color = base_resume.secondary_color
                self.font_family = base_resume.font_family

    resume_proxy = ResumeProxy(tailored.base_resume)

    # Override objective on user_profile proxy to use tailored version
    class UserProxy:
        """Wraps user but overrides objective with tailored version."""
        def __init__(self, user, objective):
            self._user = user
            self.objective = objective

        def __getattr__(self, name):
            return getattr(self._user, name)

    user_proxy = UserProxy(user, objective)

    return {
        'resume': resume_proxy,
        'user_profile': user_proxy,
        'projects': projects,
        'internships': internships,
        'work_experience': experience,
        'certifications': user.get_certifications() if hasattr(user, 'get_certifications') else [],
        'technical_skills': skills,
        'skill_rows': skill_rows,
        'linkedin_link': linkedin_link,
        'github_link': github_link,
        'website_link': website_link,
        'achievements_list': achievements_list,
        'extracurricular_html': extracurricular_html,
        'tailored': tailored,
    }


def _get_resume_template(tailored):
    """Get the HTML/CSS template for rendering. Uses base_resume template or first available."""
    if tailored.base_resume and tailored.base_resume.template:
        return tailored.base_resume.template

    # Fallback: use first active template in DB
    template = ResumeTemplate.objects.filter(is_active=True).first()
    if template:
        return template

    # Last resort: very basic HTML template
    return None


@login_required
def preview_tailored_resume(request, tailored_id):
    """Preview the AI-tailored resume in browser."""
    tailored = get_object_or_404(TailoredResume, id=tailored_id, user=request.user)
    user = request.user
    ctx = _build_tailored_context(tailored, user)

    resume_template = _get_resume_template(tailored)
    if resume_template:
        html_string = Template(resume_template.html_structure).render(Context(ctx))
        try:
            css_string = Template(resume_template.css_structure).render(Context(ctx))
        except Exception:
            css_string = ''
        full_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>{css_string}</style>
</head><body>{html_string}</body></html>"""
        return HttpResponse(full_html)

    # Fallback: render a simple HTML preview
    return HttpResponse(_render_basic_tailored_html(ctx, user), content_type='text/html')


@login_required
def download_tailored_resume(request, tailored_id):
    """Download the AI-tailored resume as PDF."""
    tailored = get_object_or_404(TailoredResume, id=tailored_id, user=request.user)
    user = request.user
    ctx = _build_tailored_context(tailored, user)

    # Resolve the resume object for colours/toggles
    resume_obj = None
    if tailored.base_resume:
        resume_obj = tailored.base_resume

    try:
        user_profile = ctx.get('user_profile', user)
        pdf_content = generate_resume_pdf(user_profile, resume=resume_obj, context=ctx)

        job_title_slug = tailored.job.title.replace(' ', '_')[:30]
        filename = f"{user.full_name.replace(' ', '_')}_Tailored_{job_title_slug}.pdf"
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf_content)
        return response

    except Exception as e:
        import logging
        logging.error(f'Tailored resume download error: {str(e)}')
        return HttpResponse(f'Error generating tailored resume: {str(e)}', status=500)


def _render_basic_tailored_html(ctx, user):
    """Render a basic HTML resume when no template is available."""
    skills = ctx.get('technical_skills', [])
    objective = ctx.get('user_profile', user).objective or ''
    experience = ctx.get('work_experience', [])
    projects = ctx.get('projects', [])
    certs = ctx.get('certifications', [])

    skills_html = ''.join(f'<span class="skill-item">{s}</span>' for s in skills)

    exp_html = ''
    for job in experience:
        exp_html += f"""<div class="experience-item">
            <div class="exp-header"><h4>{job.get('title', '')}</h4>
            <span>{job.get('start_date', '')} – {job.get('end_date', 'Present')}</span></div>
            <p class="exp-company">{job.get('company', '')}</p>
            <div>{job.get('description', '')}</div>
        </div>"""

    proj_html = ''
    for p in projects:
        proj_html += f"""<div class="project-item">
            <h4>{p.get('title', '')}</h4>
            <div>{p.get('description', '')}</div>
            <div class="project-tech"><em>{p.get('technologies', '')}</em></div>
        </div>"""

    cert_html = ''
    for c in certs:
        cert_html += f"""<div class="cert-item">
            <h4>{c.get('name', '')}</h4>
            <small>{c.get('issuing_organization', '')} {c.get('date', '')}</small>
        </div>"""

    return f"""<div class="resume-container">
        <header class="resume-header">
            <h1>{user.full_name}</h1>
            <div class="contact-info">
                {user.email or ''} | {user.phone_number or ''}
            </div>
        </header>
        {'<section class="resume-section"><h3 class="section-title">Professional Summary</h3><p>' + objective + '</p></section>' if objective else ''}
        {'<section class="resume-section"><h3 class="section-title">Technical Skills</h3><div class="skills-grid">' + skills_html + '</div></section>' if skills else ''}
        {'<section class="resume-section"><h3 class="section-title">Work Experience</h3>' + exp_html + '</section>' if experience else ''}
        {'<section class="resume-section"><h3 class="section-title">Projects</h3>' + proj_html + '</section>' if projects else ''}
        {'<section class="resume-section"><h3 class="section-title">Certifications</h3>' + cert_html + '</section>' if certs else ''}
    </div>"""


