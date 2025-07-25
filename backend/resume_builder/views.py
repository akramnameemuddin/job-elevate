from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
import json
import os
from weasyprint import HTML, CSS
from io import BytesIO

from accounts.models import User
from .models import ResumeTemplate, Resume
from django.template import Template, Context


@login_required
def resume_dashboard(request):
    """Show all user resumes and template options"""
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
    
    context = {
        'user_resumes': user_resumes,
        'resume_templates': resume_templates,
        'user_initials': initials,
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

    return HttpResponse(html_string)

@login_required
def download_resume(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    user = request.user

    # Prepare projects
    projects = user.get_projects()
    for project in projects:
        if project.get('technologies'):
            project['tech_list'] = [tech.strip() for tech in project['technologies'].split(',')]
        else:
            project['tech_list'] = []

        if project.get('description'):
            project['description'] = project['description'].replace('\n', '<br>')

    # Process experiences
    internships = user.get_internships()
    for internship in internships:
        if internship.get('description'):
            internship['description'] = internship['description'].replace('\n', '<br>')

    work_experience = user.get_work_experience()
    for job in work_experience:
        if job.get('description'):
            job['description'] = job['description'].replace('\n', '<br>')
    # Preprocess contact links
    linkedin_link = f'<a href="{user.linkedin_profile}" target="_blank">{user.linkedin_profile}</a>' if user.linkedin_profile else ''
    github_link = f'<a href="{user.github_profile}" target="_blank">{user.github_profile}</a>' if user.github_profile else ''
    website_link = f'<a href="{user.portfolio_website}" target="_blank">{user.portfolio_website}</a>' if user.portfolio_website else ''

    # Preprocess skills into rows of 3
    skills = user.get_skills_list()
    skill_rows = [skills[i:i+3] for i in range(0, len(skills), 3)]

    # Achievements
    achievements_list = []
    if hasattr(user, 'achievements') and user.achievements:
        achievements_list = [a.strip() for a in user.achievements.split('\n') if a.strip()]

    # Extracurricular HTML
    extracurricular_html = user.extracurricular_activities.replace('\n', '<br>') if user.extracurricular_activities else ''

    context = Context({
        'resume': resume,
        'user_profile': user,
        'projects': projects,
        'internships': internships,
        'work_experience': work_experience,
        'certifications': user.get_certifications(),
        'technical_skills': skills,
        'skill_rows': skill_rows,
        'linkedin_link': linkedin_link,
        'github_link': github_link,
        'website_link': website_link,
        'achievements_list': achievements_list,
        'extracurricular_html': extracurricular_html,
        'is_download': True
    })

    html_template = Template(resume.template.html_structure)
    html_string = html_template.render(context)

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    css = CSS(string=resume.template.css_structure)
    pdf_file = BytesIO()
    html.write_pdf(pdf_file, stylesheets=[css])

    resume.download_count += 1
    resume.last_downloaded = timezone.now()

    if not resume.pdf_file:
        from django.core.files.base import ContentFile
        filename = f"{user.username}_resume_{resume.id}.pdf"
        resume.pdf_file.save(filename, ContentFile(pdf_file.getvalue()), save=True)
    else:
        resume.save()

    pdf_file.seek(0)
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{user.username}_resume_{resume.id}.pdf"'
    return response

@login_required
def delete_resume(request, resume_id):
    """Delete a resume"""
    if request.method == 'POST':
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        resume.delete()
        messages.success(request, "Resume deleted successfully!")
    return redirect('/resume_builder/')

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