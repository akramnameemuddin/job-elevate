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
    
    # Per-item selection (None = all included; list of indices = selected subset)
    selected_projects = models.JSONField(
        default=None, null=True, blank=True,
        help_text='Indices of projects to include (null = all)')
    selected_internships = models.JSONField(
        default=None, null=True, blank=True,
        help_text='Indices of internships to include (null = all)')
    selected_experience = models.JSONField(
        default=None, null=True, blank=True,
        help_text='Indices of work-experience entries to include (null = all)')
    selected_certifications = models.JSONField(
        default=None, null=True, blank=True,
        help_text='Indices of certifications to include (null = all)')

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


class TailoredResume(models.Model):
    """
    AI-tailored version of a resume for a specific job application.
    The AI agent compares the user's base resume data against the job
    requirements and produces actionable suggestions + a tailored snapshot.
    """
    STATUS_CHOICES = [
        ('analyzing', 'AI Analyzing'),
        ('reviewed', 'Suggestions Ready'),
        ('applied', 'Suggestions Applied'),
        ('submitted', 'Application Submitted'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tailored_resumes')
    base_resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='tailored_versions')
    job = models.ForeignKey('recruiter.Job', on_delete=models.CASCADE, related_name='tailored_resumes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='analyzing')

    # AI-generated suggestions stored as JSON list
    # Each item: {"id": str, "section": str, "type": "add"|"improve"|"reorder"|"remove",
    #             "priority": "high"|"medium"|"low", "current": str, "suggested": str,
    #             "reason": str, "accepted": bool|None}
    suggestions = models.JSONField(default=list, blank=True)

    # Tailored content snapshots (applied suggestions)
    tailored_objective = models.TextField(blank=True, null=True)
    tailored_skills = models.JSONField(default=list, blank=True,
                                       help_text='Skills list after AI tailoring')
    tailored_experience = models.JSONField(default=list, blank=True,
                                           help_text='Work experience bullet points after tailoring')
    tailored_projects = models.JSONField(default=list, blank=True,
                                         help_text='Projects list after tailoring')

    # ── Section-item selection (None = all included; list of indices = selected)
    selected_projects = models.JSONField(
        default=None, null=True, blank=True,
        help_text='Indices of projects to include in this tailored resume (null = all)')
    selected_internships = models.JSONField(
        default=None, null=True, blank=True,
        help_text='Indices of internships to include (null = all)')
    selected_experience = models.JSONField(
        default=None, null=True, blank=True,
        help_text='Indices of work-experience entries to include (null = all)')
    selected_certifications = models.JSONField(
        default=None, null=True, blank=True,
        help_text='Indices of certifications to include (null = all)')
    selected_skills = models.JSONField(
        default=None, null=True, blank=True,
        help_text='Skill names to include (null = all)')

    # Matching analytics
    match_score_before = models.IntegerField(default=0, help_text='Match % before tailoring')
    match_score_after = models.IntegerField(default=0, help_text='Match % after applying suggestions')
    keywords_matched = models.JSONField(default=list, blank=True,
                                        help_text='Keywords from job found in tailored resume')
    keywords_missing = models.JSONField(default=list, blank=True,
                                        help_text='Job keywords still missing after tailoring')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'job', 'base_resume')

    def __str__(self):
        return f"Tailored resume for {self.user} → {self.job.title}"

    @property
    def accepted_suggestions(self):
        return [s for s in (self.suggestions or []) if s.get('accepted') is True]

    @property
    def pending_suggestions(self):
        return [s for s in (self.suggestions or []) if s.get('accepted') is None]

    @property
    def suggestion_counts(self):
        sug = self.suggestions or []
        accepted = len([s for s in sug if s.get('accepted') is True])
        rejected = len([s for s in sug if s.get('accepted') is False])
        total = len(sug)
        return {
            'total': total,
            'high': len([s for s in sug if s.get('priority') == 'high']),
            'medium': len([s for s in sug if s.get('priority') == 'medium']),
            'low': len([s for s in sug if s.get('priority') == 'low']),
            'accepted': accepted,
            'rejected': rejected,
            'pending': total - accepted - rejected,
        }