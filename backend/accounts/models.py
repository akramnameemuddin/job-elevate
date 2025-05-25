# --- accounts/models.py ---
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import json

class User(AbstractUser):
    full_name = models.CharField(_('full name'), max_length=255)
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True, null=True)
    email = models.EmailField(_('email address'), unique=True)
    profile_photo = models.ImageField(_('profile photo'), upload_to='profile_photos/', blank=True, null=True)
    linkedin_profile = models.URLField(_('LinkedIn profile'), blank=True, null=True)
    github_profile = models.URLField(_('GitHub profile'), blank=True, null=True)
    portfolio_website = models.URLField(_('portfolio website'), blank=True, null=True)
    # Add these fields to your User model
    email_verified = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    USER_TYPE_CHOICES = [
        ('student', _('Student')),
        ('professional', _('Professional')),
        ('recruiter', _('Recruiter'))
    ]
    user_type = models.CharField(_('user type'), max_length=20, choices=USER_TYPE_CHOICES, default='student')
    objective = models.TextField(_('career objective'), blank=True, null=True)
    university = models.CharField(_('university'), max_length=255, blank=True, null=True)
    degree = models.CharField(_('degree'), max_length=100, blank=True, null=True)
    graduation_year = models.IntegerField(_('graduation year'), blank=True, null=True)
    cgpa = models.FloatField(_('CGPA'), blank=True, null=True)
    technical_skills = models.TextField(_('technical skills'), blank=True, null=True)
    soft_skills = models.TextField(_('soft skills'), blank=True, null=True)
    
    # Updated field - now stores JSON data
    projects = models.TextField(_('projects'), blank=True, null=True)
    
    # Updated field - now stores JSON data
    internships = models.TextField(_('internships'), blank=True, null=True)
    
    # Updated field - now stores JSON data
    certifications = models.TextField(_('certifications'), blank=True, null=True)
    
    achievements = models.TextField(_('achievements'), blank=True, null=True)
    job_title = models.CharField(_('job title'), max_length=100, blank=True, null=True)
    organization = models.CharField(_('organization'), max_length=100, blank=True, null=True)
    experience = models.IntegerField(_('years of experience'), blank=True, null=True)
    industry = models.CharField(_('industry'), max_length=100, blank=True, null=True)
    
    # Updated field - now stores JSON data
    work_experience = models.TextField(_('work experience'), blank=True, null=True)
    work_experience_description = models.TextField(_('Work Experience Details'), blank=True, null=True)

    
    extracurricular_activities = models.TextField(_('extracurricular activities'), blank=True, null=True)
    company_name = models.CharField(_('company name'), max_length=255, blank=True, null=True)
    company_website = models.URLField(_('company website'), blank=True, null=True)
    company_description = models.TextField(_('company description'), blank=True, null=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.full_name or self.username

    def get_skills_list(self):
        return [skill.strip() for skill in self.technical_skills.split(',')] if self.technical_skills else []

    def get_internships(self):
        """Returns internships as a list of dictionaries"""
        if not self.internships or not self.internships.strip():
            return []
        try:
            return json.loads(self.internships)
        except json.JSONDecodeError:
            # If the field contains old format data
            return [{"title": "Previous Experience", "description": self.internships}]
    
    def get_work_experience(self):
        """Returns work experience as a list of dictionaries"""
        if not self.work_experience or not self.work_experience.strip():
            return []
        try:
            return json.loads(self.work_experience)
        except json.JSONDecodeError:
            # If the field contains old format data
            return [{"title": "Previous Experience", "description": self.work_experience}]
    
    def get_certifications(self):
        """Returns certifications as a list of dictionaries"""
        if not self.certifications or not self.certifications.strip():
            return []
        try:
            return json.loads(self.certifications)
        except json.JSONDecodeError:
            # If the field contains old format data
            return [{"name": "Previous Certification", "description": self.certifications}]
    
    def get_projects(self):
        """Returns projects as a list of dictionaries"""
        if not self.projects or not self.projects.strip():
            return []
        try:
            return json.loads(self.projects)
        except json.JSONDecodeError:
            # If the field contains old format data
            return [{"title": "Previous Project", "description": self.projects}]

    def clean(self):
        super().clean()
        if self.technical_skills:
            skills = [skill.strip() for skill in self.technical_skills.split(',') if skill.strip()]
            self.technical_skills = ', '.join(skills)
            
    def profile_completion(self):
        def is_filled(value):
            if not value:
                return False
            string_val = str(value).strip()
            if string_val in ('', '[]', '{}', 'null', 'None'):
                return False
            return True

        # Common fields for both user types
        fields = [
            self.full_name,
            self.phone_number,
            self.email,
            self.profile_photo,
            self.linkedin_profile,
            self.github_profile,
            self.portfolio_website,
            self.objective,
            self.university,
            self.degree,
            self.graduation_year,
            self.cgpa,
            self.technical_skills,
            self.soft_skills,
            self.projects,
            self.certifications,
            self.achievements,
            self.extracurricular_activities,
        ]

        # Add user-specific fields
        if self.user_type == 'student': 
            fields.append(self.internships)
        elif self.user_type == 'professional':
            fields.append(self.work_experience_description)
            fields.append(self.job_title)
            fields.append(self.organization)
            fields.append(self.industry)

        total = len(fields)
        filled = sum(1 for f in fields if is_filled(f))

        return int((filled / total) * 100) if total > 0 else 0


class RecruiterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiterprofile')
    company_name = models.CharField(max_length=255)
    company_website = models.URLField(blank=True, null=True)
    company_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.company_name