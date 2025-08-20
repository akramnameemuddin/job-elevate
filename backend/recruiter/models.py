from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from accounts.models import User

class Job(models.Model):
    """Model for job postings created by recruiters"""
    JOB_STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('Paused', 'Paused'),
        ('Filled', 'Filled'),
    ]
    
    JOB_TYPE_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Internship', 'Internship'),
        ('Remote', 'Remote'),
        ('Contract', 'Contract'),
        ('Freelance', 'Freelance'),
    ]
    
    title = models.CharField(_('job title'), max_length=255)
    company = models.CharField(_('company'), max_length=255)
    location = models.CharField(_('location'), max_length=255)
    job_type = models.CharField(_('job type'), max_length=50, choices=JOB_TYPE_CHOICES)
    salary = models.CharField(_('salary range'), max_length=100, blank=True, null=True)
    experience = models.IntegerField(_('experience required (years)'), default=0)
    description = models.TextField(_('job description'))
    requirements = models.TextField(_('job requirements'), blank=True, null=True)
    status = models.CharField(_('job status'), max_length=10, choices=JOB_STATUS_CHOICES, default='Open')
    skills = models.JSONField(_('required skills'), default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posted_jobs',
        limit_choices_to={'user_type': 'recruiter'}
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('job')
        verbose_name_plural = _('jobs')
    
    def __str__(self):
        return f"{self.title} at {self.company}"
    
    @property
    def applicant_count(self):
        return self.applications.count()


class Application(models.Model):
    """Model for job applications submitted by users"""
    APPLICATION_STATUS_CHOICES = [
        ('Applied', 'Applied'),
        ('Shortlisted', 'Shortlisted'),
        ('Rejected', 'Rejected'),
        ('Interview', 'Interview'),
        ('Offered', 'Offered'),
        ('Hired', 'Hired'),
    ]
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        limit_choices_to={'user_type__in': ['student', 'professional']}
    )
    status = models.CharField(
        _('application status'),
        max_length=20,
        choices=APPLICATION_STATUS_CHOICES,
        default='Applied'
    )
    match_score = models.IntegerField(_('match score'), default=0)
    cover_letter = models.TextField(_('cover letter'), blank=True, null=True)
    resume = models.FileField(_('resume'), upload_to='resumes/', blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-applied_at']
        unique_together = ('job', 'applicant')
        verbose_name = _('application')
        verbose_name_plural = _('applications')
    
    def __str__(self):
        return f"{self.applicant} - {self.job}"
    
    def calculate_match_score(self):
        """Calculate match score based on applicant skills and job requirements"""
        job_skills = self.job.skills
        applicant_skills = self.applicant.get_skills_list()
        
        if not job_skills or not applicant_skills:
            return 0
        
        # Count matching skills
        matching_skills = [skill for skill in applicant_skills if skill in job_skills]
        
        # Calculate score (percentage of job skills matched)
        try:
            score = int((len(matching_skills) / len(job_skills)) * 100)
            return min(score, 100)  # Cap at 100%
        except ZeroDivisionError:
            return 0
    
    def save(self, *args, **kwargs):
        if not self.match_score:
            self.match_score = self.calculate_match_score()
        super().save(*args, **kwargs)


class Message(models.Model):
    """Model for messages between recruiters and applicants"""
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='messages',
        blank=True,
        null=True
    )
    subject = models.CharField(_('subject'), max_length=255)
    content = models.TextField(_('message content'))
    is_read = models.BooleanField(_('read status'), default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = _('message')
        verbose_name_plural = _('messages')
    
    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}: {self.subject}"