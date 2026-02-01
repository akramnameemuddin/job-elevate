from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from assessments.models import Skill


class Course(models.Model):
    """Available courses for skill development"""
    COURSE_TYPE_CHOICES = [
        ('video', _('Video Course')),
        ('interactive', _('Interactive Course')),
        ('reading', _('Reading Material')),
        ('project', _('Hands-on Project')),
        ('workshop', _('Workshop')),
    ]

    DIFFICULTY_CHOICES = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
    ]

    PLATFORM_CHOICES = [
        ('internal', _('JobElevate')),
        ('coursera', _('Coursera')),
        ('udemy', _('Udemy')),
        ('edx', _('edX')),
        ('linkedin', _('LinkedIn Learning')),
        ('youtube', _('YouTube')),
        ('other', _('Other')),
    ]

    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_('skill')
    )
    course_type = models.CharField(
        _('course type'),
        max_length=20,
        choices=COURSE_TYPE_CHOICES,
        default='video'
    )
    difficulty_level = models.CharField(
        _('difficulty level'),
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner'
    )
    platform = models.CharField(
        _('platform'),
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='internal'
    )
    url = models.URLField(
        _('course URL'),
        max_length=500,
        validators=[URLValidator()],
        blank=True
    )
    duration_hours = models.FloatField(
        _('duration (hours)'),
        default=0,
        validators=[MinValueValidator(0)]
    )
    duration_weeks = models.IntegerField(
        _('duration (weeks)'),
        default=0,
        help_text="Estimated weeks to complete"
    )
    target_proficiency_level = models.FloatField(
        _('target proficiency level'),
        default=5.0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Expected proficiency after completion (1-10)"
    )
    
    # Metadata
    instructor = models.CharField(_('instructor'), max_length=255, blank=True)
    thumbnail = models.URLField(_('thumbnail URL'), max_length=500, blank=True)
    rating = models.FloatField(
        _('rating'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    is_free = models.BooleanField(_('free'), default=True)
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True
    )
    is_active = models.BooleanField(_('active'), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        ordering = ['-rating', 'title']

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_level_display()})"

    @property
    def enrollment_count(self):
        """Get number of users enrolled"""
        return CourseProgress.objects.filter(course=self).count()


class SkillGap(models.Model):
    """Identified skill gaps for users"""
    PRIORITY_CHOICES = [
        ('critical', _('Critical')),
        ('high', _('High')),
        ('moderate', _('Moderate')),
        ('low', _('Low')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_gaps',
        verbose_name=_('user')
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='user_gaps',
        verbose_name=_('skill')
    )
    current_level = models.FloatField(
        _('current level'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    required_level = models.FloatField(
        _('required level'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    gap_value = models.FloatField(
        _('gap value'),
        default=0,
        help_text="Required - Current"
    )
    gap_severity = models.FloatField(
        _('gap severity'),
        default=0,
        help_text="(Required - Current) / Required"
    )
    priority = models.CharField(
        _('priority'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='moderate'
    )
    priority_score = models.FloatField(
        _('priority score'),
        default=0,
        help_text="Calculated: (Gap Severity × 0.4) + (Criticality × 0.6)"
    )
    job_criticality = models.FloatField(
        _('job criticality'),
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="0.0 = optional, 1.0 = must-have"
    )
    target_job_title = models.CharField(
        _('target job title'),
        max_length=255,
        blank=True,
        help_text="Job role this gap is identified for"
    )
    related_job = models.ForeignKey(
        'recruiter.Job',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='skill_gaps',
        help_text="Specific job posting this gap relates to"
    )
    estimated_learning_hours = models.IntegerField(
        _('estimated learning hours'),
        default=0,
        help_text="Estimated time to close this gap"
    )
    identified_at = models.DateTimeField(auto_now_add=True)
    is_addressed = models.BooleanField(_('addressed'), default=False)

    class Meta:
        verbose_name = _('skill gap')
        verbose_name_plural = _('skill gaps')
        ordering = ['-priority', '-gap_value']
        unique_together = ('user', 'skill', 'target_job_title')

    def __str__(self):
        return f"{self.user.username} - {self.skill.name} (Gap: {self.gap_value})"

    def save(self, *args, **kwargs):
        # Auto-calculate gap value
        self.gap_value = self.required_level - self.current_level
        
        # Calculate gap severity (normalized)
        if self.required_level > 0:
            self.gap_severity = self.gap_value / self.required_level
        else:
            self.gap_severity = 0
        
        # Calculate priority score: (Gap Severity × 0.4) + (Job Criticality × 0.6)
        self.priority_score = (self.gap_severity * 0.4) + (self.job_criticality * 0.6)
        
        # Auto-assign priority based on priority score
        if self.priority_score >= 0.7 or self.gap_value >= 4:
            self.priority = 'critical'
        elif self.priority_score >= 0.5 or self.gap_value >= 2:
            self.priority = 'high'
        elif self.priority_score >= 0.3 or self.gap_value >= 1:
            self.priority = 'moderate'
        else:
            self.priority = 'low'
        
        # Estimate learning hours (rough formula: 10 hours per proficiency point)
        if self.estimated_learning_hours == 0:
            self.estimated_learning_hours = int(self.gap_value * 10)
        
        super().save(*args, **kwargs)
    
    def get_priority_emoji(self):
        """Visual indicator for priority"""
        return {
            'critical': '🔴',
            'high': '🟡',
            'moderate': '🟠',
            'low': '🟢'
        }.get(self.priority, '⚪')


class LearningPath(models.Model):
    """Personalized learning roadmap for users"""
    STATUS_CHOICES = [
        ('not_started', _('Not Started')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('paused', _('Paused')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_paths',
        verbose_name=_('user')
    )
    skill_gap = models.ForeignKey(
        SkillGap,
        on_delete=models.CASCADE,
        related_name='learning_paths',
        verbose_name=_('skill gap')
    )
    title = models.CharField(
        _('title'),
        max_length=255,
        help_text="e.g., 'Python Mastery Path for Data Analyst'"
    )
    description = models.TextField(_('description'), blank=True)
    
    # Courses in this path (ordered list of course IDs)
    courses = models.ManyToManyField(
        Course,
        through='LearningPathCourse',
        related_name='learning_paths',
        verbose_name=_('courses')
    )
    
    estimated_weeks = models.IntegerField(
        _('estimated weeks'),
        default=0,
        help_text="Total time to complete path"
    )
    estimated_hours = models.FloatField(
        _('estimated hours'),
        default=0
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )
    
    progress_percentage = models.FloatField(
        _('progress (%)'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('learning path')
        verbose_name_plural = _('learning paths')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def update_progress(self):
        """Calculate progress based on completed courses"""
        path_courses = self.learningpathcourse_set.all()
        total = path_courses.count()
        
        if total == 0:
            self.progress_percentage = 0
        else:
            completed = sum(1 for pc in path_courses if pc.is_completed)
            self.progress_percentage = (completed / total) * 100
            
            if self.progress_percentage == 100:
                self.status = 'completed'
                if not self.completed_at:
                    from django.utils import timezone
                    self.completed_at = timezone.now()
            elif self.progress_percentage > 0:
                self.status = 'in_progress'
                if not self.started_at:
                    from django.utils import timezone
                    self.started_at = timezone.now()
        
        self.save()


class LearningPathCourse(models.Model):
    """Through model for ordering courses in learning paths"""
    learning_path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        verbose_name=_('learning path')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name=_('course')
    )
    order = models.IntegerField(_('order'), default=0)
    is_completed = models.BooleanField(_('completed'), default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('learning path course')
        verbose_name_plural = _('learning path courses')
        ordering = ['learning_path', 'order']
        unique_together = ('learning_path', 'course')

    def __str__(self):
        return f"{self.learning_path.title} - {self.course.title} (#{self.order})"


class CourseProgress(models.Model):
    """Track user's progress in individual courses"""
    STATUS_CHOICES = [
        ('enrolled', _('Enrolled')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('dropped', _('Dropped')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_progress',
        verbose_name=_('user')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='user_progress',
        verbose_name=_('course')
    )
    learning_path = models.ForeignKey(
        LearningPath,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='course_progress',
        verbose_name=_('learning path')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='enrolled'
    )
    
    progress_percentage = models.FloatField(
        _('progress (%)'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    time_spent_hours = models.FloatField(
        _('time spent (hours)'),
        default=0
    )
    
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(auto_now=True)
    
    # Notes and bookmarks
    notes = models.TextField(_('notes'), blank=True)
    
    # Certificate
    certificate_earned = models.BooleanField(_('certificate earned'), default=False)
    certificate_url = models.URLField(_('certificate URL'), max_length=500, blank=True)

    class Meta:
        verbose_name = _('course progress')
        verbose_name_plural = _('course progress')
        ordering = ['-last_accessed_at']
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.progress_percentage}%)"

    def mark_completed(self):
        """Mark course as completed"""
        from django.utils import timezone
        
        self.status = 'completed'
        self.progress_percentage = 100
        self.completed_at = timezone.now()
        self.save()
        
        # Update learning path progress if part of one
        if self.learning_path:
            path_course = LearningPathCourse.objects.filter(
                learning_path=self.learning_path,
                course=self.course
            ).first()
            
            if path_course:
                path_course.is_completed = True
                path_course.completed_at = timezone.now()
                path_course.save()
                
                self.learning_path.update_progress()
