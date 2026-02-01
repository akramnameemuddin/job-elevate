# --- accounts/models.py ---
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import json

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.

    Provides additional fields for user profiles including contact information,
    social media profiles, email verification, and user type classification.
    """
    full_name = models.CharField(_('full name'), max_length=255)
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True, null=True)
    email = models.EmailField(_('email address'), unique=True)
    profile_photo = models.ImageField(_('profile photo'), upload_to='profile_photos/', blank=True, null=True)
    linkedin_profile = models.URLField(_('LinkedIn profile'), blank=True, null=True)
    github_profile = models.URLField(_('GitHub profile'), blank=True, null=True)
    portfolio_website = models.URLField(_('portfolio website'), blank=True, null=True)

    # Email verification fields
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
        """Get technical skills as a list"""
        return [skill.strip() for skill in self.technical_skills.split(',')] if self.technical_skills else []
    
    def get_soft_skills_list(self):
        """Get soft skills as a list"""
        return [skill.strip() for skill in self.soft_skills.split(',')] if self.soft_skills else []
    
    def get_all_skills_list(self):
        """Get combined list of technical and soft skills"""
        all_skills = []
        if self.technical_skills:
            all_skills.extend([skill.strip() for skill in self.technical_skills.split(',') if skill.strip()])
        if self.soft_skills:
            all_skills.extend([skill.strip() for skill in self.soft_skills.split(',') if skill.strip()])
        return all_skills

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

    def get_job_matches_count(self, match_threshold=0.3):
        """
        Calculate the number of jobs that match user's skills
        
        Args:
            match_threshold (float): Minimum percentage of skill overlap required (default: 30%)
        
        Returns:
            int: Number of matching jobs
        """
        if self.user_type not in ['student', 'professional']:
            return 0
            
        try:
            from recruiter.models import Job
            
            user_skills = self.get_skills_list()
            if not user_skills:
                return 0
                
            user_skills_set = set([skill.lower().strip() for skill in user_skills])
            match_count = 0
            
            open_jobs = Job.objects.filter(status='Open')
            
            for job in open_jobs:
                if job.skills:
                    # Handle both old format (strings) and new format (dicts)
                    job_skills_list = []
                    for skill in job.skills:
                        if isinstance(skill, dict):
                            job_skills_list.append(skill.get('name', '').lower().strip())
                        else:
                            job_skills_list.append(skill.lower().strip())
                    
                    job_skills_set = set(job_skills_list)
                    
                    if job_skills_set:
                        matching_skills = user_skills_set.intersection(job_skills_set)
                        match_percentage = len(matching_skills) / len(job_skills_set)
                        
                        if match_percentage >= match_threshold:
                            match_count += 1
                            
            return match_count
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating job matches for user {self.id}: {str(e)}")
            return 0
    
    def calculate_job_fit_score(self, job):
        """
        Calculate job fit score based on verified skills vs job requirements
        
        Formula: (matched_skills / total_required_skills) × 100
        Enhanced with:
        - Proficiency level matching
        - Skill weight importance
        - Experience multipliers
        
        Args:
            job: Job instance to calculate fit against
        
        Returns:
            dict: {
                'score': float (0-100),
                'matched_skills': list,
                'missing_skills': list,
                'weak_skills': list (have but below required level)
            }
        """
        from assessments.models import UserSkillProfile
        
        # Get user's verified skills
        user_skills = UserSkillProfile.objects.filter(user=self).select_related('skill')
        user_skill_dict = {
            profile.skill.name.lower(): profile.verified_level 
            for profile in user_skills
        }
        
        # Get job required skills
        if not job.skills:
            return {'score': 0, 'matched_skills': [], 'missing_skills': [], 'weak_skills': []}
        
        required_skills = job.skills  # Assuming it's a list
        total_required = len(required_skills)
        
        if total_required == 0:
            return {'score': 100, 'matched_skills': [], 'missing_skills': [], 'weak_skills': []}
        
        matched_skills = []
        missing_skills = []
        weak_skills = []
        
        # Default required proficiency for jobs
        default_required_proficiency = {
            'Entry Level': 4.0,
            'Mid Level': 6.0,
            'Senior': 8.0
        }.get(getattr(job, 'experience_level', 'Mid Level'), 6.0)
        
        for skill_name in required_skills:
            skill_lower = skill_name.lower().strip()
            
            if skill_lower in user_skill_dict:
                user_level = user_skill_dict[skill_lower]
                
                # Check if proficiency meets requirement
                if user_level >= default_required_proficiency:
                    matched_skills.append({
                        'name': skill_name,
                        'level': user_level,
                        'status': 'strong'
                    })
                else:
                    weak_skills.append({
                        'name': skill_name,
                        'current': user_level,
                        'required': default_required_proficiency,
                        'gap': default_required_proficiency - user_level
                    })
            else:
                missing_skills.append({
                    'name': skill_name,
                    'required': default_required_proficiency
                })
        
        # Calculate base score
        matched_count = len(matched_skills)
        weak_count = len(weak_skills)
        
        # Give partial credit for weak skills (0.5 credit)
        effective_matched = matched_count + (weak_count * 0.5)
        base_score = (effective_matched / total_required) * 100
        
        # Experience multiplier (optional enhancement)
        experience_years = self.experience or 0
        if experience_years >= 5:
            base_score = min(base_score * 1.1, 100)  # 10% bonus
        elif experience_years >= 3:
            base_score = min(base_score * 1.05, 100)  # 5% bonus
        
        return {
            'score': round(base_score, 1),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'weak_skills': weak_skills,
            'total_required': total_required,
            'matched_count': matched_count
        }