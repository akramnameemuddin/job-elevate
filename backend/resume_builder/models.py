from django.db import models
from django.conf import settings
from accounts.models import User
from colorfield.fields import ColorField

class ResumeTemplate(models.Model):
    """Model for resume templates"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    preview_image = models.ImageField(upload_to='resume_templates/')
    html_structure = models.TextField()
    css_structure = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Resume(models.Model):
    """Model for user generated resumes"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    template = models.ForeignKey(ResumeTemplate, on_delete=models.CASCADE, related_name='used_in_resumes')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Color scheme and style customizations
    primary_color = ColorField(default='#1565C0')
    secondary_color = ColorField(default='#03A9F4')
    font_family = models.CharField(max_length=100, default='Roboto, sans-serif')
    
    # Resume sections visibility toggles
    show_contact = models.BooleanField(default=True)
    show_links = models.BooleanField(default=True)
    show_objective = models.BooleanField(default=True)
    show_education = models.BooleanField(default=True)
    show_skills = models.BooleanField(default=True)
    show_experience = models.BooleanField(default=True)
    show_projects = models.BooleanField(default=True)
    show_certifications = models.BooleanField(default=True)
    show_achievements = models.BooleanField(default=True)
    show_extracurricular = models.BooleanField(default=True)
    
    # Additional resume metadata
    pdf_file = models.FileField(upload_to='resume_pdfs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_downloaded = models.DateTimeField(blank=True, null=True)
    download_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.full_name}'s Resume - {self.title}"
    
    class Meta:
        ordering = ['-updated_at']