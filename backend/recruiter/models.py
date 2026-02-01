from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
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
        """Calculate match score based on applicant skills (technical + soft) and job requirements"""
        job_skills = self.job.skills
        # Combine technical and soft skills
        all_applicant_skills = self.applicant.get_all_skills_list()
        
        if not job_skills or not all_applicant_skills:
            return 0
        
        # Convert to lowercase for case-insensitive matching
        # Handle both dict format {'name': 'Python'} and string format 'Python'
        job_skills_lower = []
        for skill in job_skills:
            if isinstance(skill, dict):
                skill_name = skill.get('name', '')
                if skill_name:
                    job_skills_lower.append(skill_name.lower().strip())
            elif isinstance(skill, str):
                job_skills_lower.append(skill.lower().strip())
        
        applicant_skills_lower = [skill.lower().strip() for skill in all_applicant_skills]
        
        # Count matching skills
        matching_skills = sum(1 for skill in applicant_skills_lower if skill in job_skills_lower)
        
        # Calculate score (percentage of job skills matched)
        try:
            score = int((matching_skills / len(job_skills_lower)) * 100)
            return min(score, 100)  # Cap at 100%
        except (ZeroDivisionError, TypeError):
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
        return f"{self.sender} → {self.recipient}: {self.subject}"


class JobSkillRequirement(models.Model):
    """Job skill requirements with proficiency levels and criticality"""
    SKILL_TYPE_CHOICES = [
        ('must_have', _('Must Have')),
        ('important', _('Important')),
        ('nice_to_have', _('Nice to Have')),
    ]
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='skill_requirements',
        verbose_name=_('job')
    )
    skill = models.ForeignKey(
        'assessments.Skill',
        on_delete=models.CASCADE,
        related_name='job_requirements',
        verbose_name=_('skill')
    )
    required_proficiency = models.FloatField(
        _('required proficiency level'),
        default=5.0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Required skill level (0-10 scale)"
    )
    criticality = models.FloatField(
        _('criticality'),
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="0.0 = nice-to-have, 0.5 = important, 1.0 = must-have"
    )
    is_mandatory = models.BooleanField(
        _('mandatory'),
        default=False,
        help_text="Whether this skill is absolutely required for job eligibility"
    )
    skill_type = models.CharField(
        _('skill type'),
        max_length=20,
        choices=SKILL_TYPE_CHOICES,
        default='important',
        help_text="Classification of skill importance"
    )
    weight = models.FloatField(
        _('weight'),
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(3.0)],
        help_text="Importance multiplier for matching algorithm"
    )
    years_required = models.IntegerField(
        _('years of experience required'),
        default=0,
        validators=[MinValueValidator(0)]
    )
    description = models.TextField(
        _('skill requirement description'),
        blank=True,
        help_text="Specific requirements or context for this skill"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('job skill requirement')
        verbose_name_plural = _('job skill requirements')
        ordering = ['-criticality', '-required_proficiency']
        unique_together = ('job', 'skill')

    def __str__(self):
        return f"{self.job.title} requires {self.skill.name} at {self.required_proficiency}/10"
    
    def get_criticality_display_text(self):
        """Get human-readable criticality level"""
        if self.skill_type == 'must_have':
            return "Must Have"
        elif self.skill_type == 'important':
            return "Important"
        else:
            return "Nice to Have"
    
    def evaluate_user_proficiency(self, user_skill_profile):
        """
        Evaluate how user's proficiency compares to requirement.
        Args:
            user_skill_profile: UserSkillProfile instance
        Returns:
            dict with gap analysis
        """
        user_level = user_skill_profile.verified_level if user_skill_profile else 0
        gap = self.required_proficiency - user_level
        
        if gap <= 0:
            status = "Qualified"
            color = "success"
        elif gap <= 1:
            status = "Almost Qualified"
            color = "warning"
        elif gap <= 2:
            status = "Moderate Gap"
            color = "info"
        else:
            status = "Significant Gap"
            color = "danger"
        
        return {
            'skill_name': self.skill.name,
            'required': round(self.required_proficiency, 1),
            'current': round(user_level, 1),
            'gap': round(max(gap, 0), 1),
            'gap_percentage': round((gap / self.required_proficiency * 100) if self.required_proficiency > 0 else 0, 1),
            'status': status,
            'color': color,
            'is_qualified': gap <= 0,
            'is_mandatory': self.is_mandatory,
            'criticality': self.get_criticality_display_text(),
            'weight': self.weight
        }


class UserJobFitScore(models.Model):
    """Calculate and track how well a user matches a job"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_fit_scores',
        verbose_name=_('user')
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='user_fit_scores',
        verbose_name=_('job')
    )
    overall_score = models.FloatField(
        _('overall fit score'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall job match percentage (0-100)"
    )
    skill_match_score = models.FloatField(
        _('skill match score'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    experience_score = models.FloatField(
        _('experience score'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Detailed breakdown
    matched_skills_count = models.IntegerField(_('matched skills'), default=0)
    total_required_skills = models.IntegerField(_('total required skills'), default=0)
    critical_gaps_count = models.IntegerField(_('critical gaps'), default=0)
    minor_gaps_count = models.IntegerField(_('minor gaps'), default=0)
    strengths_count = models.IntegerField(_('strengths'), default=0)
    
    # Recommendations
    is_good_match = models.BooleanField(_('good match'), default=False)
    recommendation = models.TextField(
        _('recommendation'),
        blank=True,
        help_text="AI-generated recommendation text"
    )
    
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('user job fit score')
        verbose_name_plural = _('user job fit scores')
        ordering = ['-overall_score']
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.username} → {self.job.title}: {self.overall_score:.1f}%"

    def calculate_fit_score(self):
        """Calculate comprehensive job fit score"""
        from assessments.models import UserSkillProfile
        from learning.models import SkillGap
        
        # Get job skill requirements
        requirements = self.job.skill_requirements.all()
        if not requirements:
            return 0
        
        # Get user's verified skills
        user_skills = UserSkillProfile.objects.filter(
            user=self.user,
            status='verified'
        ).select_related('skill')
        
        user_skill_dict = {
            us.skill_id: us.verified_level 
            for us in user_skills
        }
        
        # Calculate skill match
        total_weight = 0
        weighted_match = 0
        matched_count = 0
        critical_gaps = 0
        minor_gaps = 0
        strengths = 0
        
        for req in requirements:
            total_weight += req.weight * req.criticality
            user_level = user_skill_dict.get(req.skill_id, 0)
            
            if user_level >= req.required_proficiency:
                # User meets or exceeds requirement
                weighted_match += req.weight * req.criticality
                matched_count += 1
                strengths += 1
            elif user_level > 0:
                # User has skill but below requirement
                gap_percentage = (req.required_proficiency - user_level) / req.required_proficiency
                
                if gap_percentage > 0.4:  # >40% gap
                    critical_gaps += 1
                    # Give partial credit based on how close they are
                    weighted_match += (user_level / req.required_proficiency) * req.weight * req.criticality * 0.5
                else:  # <=40% gap
                    minor_gaps += 1
                    weighted_match += (user_level / req.required_proficiency) * req.weight * req.criticality * 0.7
                matched_count += 1
            else:
                # User doesn't have this skill at all
                if req.criticality >= 0.7 or req.is_mandatory:
                    critical_gaps += 1
                else:
                    minor_gaps += 1
        
        # Calculate final score
        if total_weight > 0:
            self.skill_match_score = (weighted_match / total_weight) * 100
        else:
            self.skill_match_score = 0
        
        # Experience score
        user_experience = getattr(self.user, 'years_of_experience', 0) or 0
        if self.job.experience > 0:
            self.experience_score = min((user_experience / self.job.experience) * 100, 100)
        else:
            self.experience_score = 100
        
        # Overall score: 70% skills + 30% experience
        self.overall_score = (self.skill_match_score * 0.7) + (self.experience_score * 0.3)
        
        # Update counters
        self.matched_skills_count = matched_count
        self.total_required_skills = requirements.count()
        self.critical_gaps_count = critical_gaps
        self.minor_gaps_count = minor_gaps
        self.strengths_count = strengths
        
        # Determine if good match
        self.is_good_match = (
            self.overall_score >= 70 and 
            self.critical_gaps_count == 0
        )
        
        # Generate recommendation
        if self.overall_score >= 85:
            self.recommendation = "Excellent match! You meet or exceed most requirements."
        elif self.overall_score >= 70:
            self.recommendation = "Good match. You meet most requirements with minor gaps."
        elif self.overall_score >= 50:
            self.recommendation = "Fair match. Consider upskilling in key areas before applying."
        else:
            self.recommendation = "Significant skill gaps. Focus on learning required skills first."
        
        self.save()
        return self.overall_score

        return f"Message from {self.sender} to {self.recipient}: {self.subject}"