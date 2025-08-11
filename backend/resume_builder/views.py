from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
import json
import os
# from weasyprint import HTML, CSS  # Temporarily commented out due to library dependency issues
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

    try:
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

        # Render HTML template with error handling
        try:
            html_template = Template(resume.template.html_structure)
            html_string = html_template.render(context)
        except Exception as e:
            return HttpResponse(f'Error rendering HTML template: {str(e)}', status=500)

        # Create combined HTML with CSS
        try:
            css_template = Template(resume.template.css_structure)
            css_content = css_template.render(context)
        except Exception as e:
            # Use basic CSS if template CSS fails
            css_content = """
            body { font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; color: #333; }
            .resume-container { max-width: 8.5in; margin: 0 auto; padding: 1in; }
            .resume-header { margin-bottom: 1rem; border-bottom: 2px solid #000; padding-bottom: 0.5rem; }
            .resume-section { margin-bottom: 1rem; }
            .section-title { font-size: 14px; font-weight: bold; margin-bottom: 0.5rem; }
            """
        
        # Create complete HTML document
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{user.full_name} - Resume</title>
    <style>
        {css_content}
        
        /* Additional PDF-specific styles */
        @page {{
            size: A4;
            margin: 0.75in;
        }}
        
        body {{
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        
        .resume-container {{
            max-width: 100%;
            margin: 0;
            padding: 0;
        }}
        
        .resume-section {{
            page-break-inside: avoid;
            margin-bottom: 1rem;
        }}
        
        h1, h2, h3, h4 {{
            page-break-after: avoid;
        }}
    </style>
</head>
<body>
    {html_string}
</body>
</html>"""

        # Try WeasyPrint first, then fallback to ReportLab
        pdf_content = None
        
        # Method 1: Try WeasyPrint
        try:
            import weasyprint
            html_doc = weasyprint.HTML(string=full_html, base_url=request.build_absolute_uri('/'))
            pdf_content = html_doc.write_pdf()
        except Exception as weasy_error:
            print(f"WeasyPrint failed: {weasy_error}")
            
            # Method 2: Fallback to ReportLab
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.units import inch
                from io import BytesIO
                import html2text
                
                # Convert HTML to plain text for ReportLab
                converter = html2text.HTML2Text()
                converter.ignore_links = True
                plain_text = converter.handle(html_string)
                
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                story = []
                
                # Add title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    textColor='#333333',
                    spaceAfter=12,
                    alignment=1  # Center alignment
                )
                story.append(Paragraph(f"{user.full_name} - Resume", title_style))
                story.append(Spacer(1, 12))
                
                # Add content paragraphs
                for line in plain_text.split('\n'):
                    if line.strip():
                        if line.startswith('#'):
                            # Headers
                            story.append(Paragraph(line.replace('#', '').strip(), styles['Heading2']))
                        else:
                            # Regular text
                            story.append(Paragraph(line.strip(), styles['Normal']))
                        story.append(Spacer(1, 6))
                
                doc.build(story)
                pdf_content = buffer.getvalue()
                buffer.close()
                
            except Exception as reportlab_error:
                print(f"ReportLab failed: {reportlab_error}")
                
                # Method 3: Last resort - basic text-based PDF
                try:
                    from reportlab.pdfgen import canvas
                    from io import BytesIO
                    
                    buffer = BytesIO()
                    p = canvas.Canvas(buffer, pagesize=A4)
                    width, height = A4
                    
                    # Simple text-based resume
                    y_position = height - 100
                    p.setFont("Helvetica-Bold", 16)
                    p.drawString(100, y_position, f"{user.full_name}")
                    
                    y_position -= 30
                    p.setFont("Helvetica", 12)
                    if user.email:
                        p.drawString(100, y_position, f"Email: {user.email}")
                        y_position -= 20
                    
                    if user.phone_number:
                        p.drawString(100, y_position, f"Phone: {user.phone_number}")
                        y_position -= 20
                    
                    if user.objective:
                        y_position -= 20
                        p.setFont("Helvetica-Bold", 14)
                        p.drawString(100, y_position, "Objective:")
                        y_position -= 20
                        p.setFont("Helvetica", 12)
                        # Simple text wrapping
                        objective_lines = [user.objective[i:i+80] for i in range(0, len(user.objective), 80)]
                        for line in objective_lines:
                            p.drawString(100, y_position, line)
                            y_position -= 15
                    
                    p.save()
                    pdf_content = buffer.getvalue()
                    buffer.close()
                    
                except Exception as final_error:
                    return HttpResponse(
                        f'All PDF generation methods failed. Final error: {str(final_error)}',
                        status=500,
                        content_type='text/plain'
                    )
        
        if pdf_content:
            # Update resume metadata
            resume.download_count += 1
            resume.last_downloaded = timezone.now()
            resume.save()

            # Return PDF response
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{user.full_name.replace(" ", "_")}_Resume.pdf"'
            response['Content-Length'] = len(pdf_content)
            
            return response
        else:
            return HttpResponse('PDF generation failed', status=500)
            
    except Exception as e:
        # General error handling
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
    if request.method == 'POST':
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        resume.delete()
        messages.success(request, "Resume deleted successfully!")
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