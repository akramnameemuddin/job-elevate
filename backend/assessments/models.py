"""
Production-Ready Skill Assessment Models
Designed for minimal AI usage, anti-cheating, and graceful degradation
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


class SkillCategory(models.Model):
    """Categories for grouping skills (e.g., Programming, Data Analysis)"""
    name = models.CharField(_('category name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    icon = models.CharField(_('icon class'), max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('skill category')
        verbose_name_plural = _('skill categories')
        ordering = ['name']

    def __str__(self):
        return self.name


class Skill(models.Model):
    """Individual skills with one-time question generation"""
    category = models.ForeignKey(
        SkillCategory,
        on_delete=models.CASCADE,
        related_name='skills',
        verbose_name=_('category')
    )
    name = models.CharField(_('skill name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    
    # NEW 100-QUESTION SYSTEM: Track question bank size
    question_count = models.IntegerField(
        _('question count'),
        default=0,
        help_text="Number of questions stored in bank (target: 100)"
    )
    
    # ANTI-TOKEN-EXHAUSTION: Track if questions were generated
    questions_generated = models.BooleanField(_('questions generated'), default=False)
    questions_generated_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('skill')
        verbose_name_plural = _('skills')
        ordering = ['category', 'name']
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    def needs_more_questions(self):
        """Check if skill needs more questions (target: 100)"""
        return self.question_count < 100
    
    def has_sufficient_questions(self):
        """Check if skill has at least 20 questions for assessment"""
        return self.question_count >= 20


class QuestionBank(models.Model):
    """
    PERSISTENT question storage - questions generated ONCE per skill via AI.
    Never deleted, always reused. This prevents AI token exhaustion.
    """
    DIFFICULTY_CHOICES = [
        ('easy', _('Easy')),
        ('medium', _('Medium')),
        ('hard', _('Hard')),
    ]
    
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='question_bank',
        verbose_name=_('skill')
    )
    question_text = models.TextField(_('question text'))
    
    # ANTI-CHEATING: Store options as JSON array
    # Example: ["Option A", "Option B", "Option C", "Option D"]
    options = models.JSONField(
        _('answer options'),
        default=list,
        help_text="List of answer options (will be shuffled per user)"
    )
    
    # ANTI-CHEATING: Store correct answer as VALUE, not index
    # Example: "Option B" (not index 1)
    correct_answer = models.TextField(
        _('correct answer'),
        help_text="Exact text of the correct option"
    )
    
    difficulty = models.CharField(
        _('difficulty'),
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )
    
    # Proficiency level (0-10 scale) for skill gap matching
    proficiency_level = models.FloatField(
        _('proficiency level'),
        default=5.0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Proficiency level this question tests (0-10)"
    )
    
    # Points awarded for correct answer
    points = models.IntegerField(
        _('points'),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    explanation = models.TextField(_('explanation'), blank=True)
    
    # Metadata
    created_by_ai = models.BooleanField(_('created by AI'), default=False)
    times_used = models.IntegerField(_('times used'), default=0)
    times_correct = models.IntegerField(_('times correct'), default=0)
    times_incorrect = models.IntegerField(_('times incorrect'), default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('question bank')
        verbose_name_plural = _('question banks')
        ordering = ['skill', 'difficulty', '?']  # Random order
        indexes = [
            models.Index(fields=['skill', 'difficulty']),
        ]

    def __str__(self):
        return f"{self.skill.name} - {self.difficulty} - {self.question_text[:50]}"
    
    @property
    def success_rate(self):
        """Calculate percentage of users who answered correctly"""
        if self.times_used == 0:
            return 0
        return round((self.times_correct / self.times_used) * 100, 1)


class Assessment(models.Model):
    """
    Lightweight assessment model - mainly a container.
    DEPRECATED in favor of direct QuestionBank usage.
    Kept for backward compatibility.
    """
    DIFFICULTY_CHOICES = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('mixed', _('Mixed')),
    ]

    title = models.CharField(_('title'), max_length=200)
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name=_('skill')
    )
    description = models.TextField(_('description'))
    difficulty_level = models.CharField(
        _('difficulty level'),
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='mixed'
    )
    duration_minutes = models.IntegerField(
        _('duration (minutes)'),
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(180)]
    )
    passing_score_percentage = models.IntegerField(
        _('passing score (%)'),
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('assessment')
        verbose_name_plural = _('assessments')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.skill.name})"


class Question(models.Model):
    """
    DEPRECATED: Questions now stored in QuestionBank.
    Kept for backward compatibility only.
    """
    DIFFICULTY_CHOICES = [
        ('easy', _('Easy')),
        ('medium', _('Medium')),
        ('hard', _('Hard')),
    ]
    
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('assessment')
    )
    question_text = models.TextField(_('question text'))
    question_type = models.CharField(_('question type'), max_length=20, default='mcq')
    difficulty = models.CharField(
        _('difficulty'),
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )
    points = models.IntegerField(
        _('points'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    order = models.IntegerField(_('order'), default=1)
    options = models.JSONField(_('options'), default=list)
    correct_answer = models.TextField(_('correct answer'))
    explanation = models.TextField(_('explanation'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('question')
        verbose_name_plural = _('questions')
        ordering = ['assessment', 'order']

    def __str__(self):
        return f"{self.assessment.title} - Q{self.order}"


class AssessmentAttempt(models.Model):
    """
    Track user's attempt at a skill assessment.
    Linked to SKILL, not Assessment (for direct QuestionBank usage).
    """
    STATUS_CHOICES = [
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('abandoned', _('Abandoned')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessment_attempts',
        verbose_name=_('user')
    )
    
    # Link to skill directly (bypassing Assessment model)
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('skill'),
        null=True,  # Nullable for backward compatibility
        blank=True
    )
    
    # Backward compatibility
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('assessment'),
        null=True,
        blank=True
    )
    
    # Store which questions were used (IDs from QuestionBank)
    question_ids = models.JSONField(
        _('question IDs'),
        default=list,
        help_text="List of QuestionBank IDs used in this attempt"
    )
    
    # Backward compatibility field for old database schema
    selected_question_ids = models.TextField(
        _('selected question IDs'),
        default='[]',
        help_text="JSON string of question IDs (backward compatibility)"
    )
    
    # Store shuffled options per question (for consistency during attempt)
    shuffled_options = models.JSONField(
        _('shuffled options'),
        default=dict,
        help_text="Mapping of question_id to shuffled options"
    )
    
    # Shuffle seed for reproducibility (backward compatibility)
    shuffle_seed = models.IntegerField(
        _('shuffle seed'),
        null=True,
        blank=True,
        help_text="Random seed used for shuffling"
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress'
    )
    
    score = models.FloatField(_('score'), default=0)
    max_score = models.FloatField(_('maximum score'), default=0)
    total_score = models.FloatField(_('total score'), default=0)  # Backward compatibility
    percentage = models.FloatField(_('percentage'), default=0)
    proficiency_level = models.FloatField(_('proficiency level'), default=0)  # Backward compatibility
    passed = models.BooleanField(_('passed'), default=False)  # Backward compatibility
    
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Time tracking
    time_spent_seconds = models.IntegerField(_('time spent (seconds)'), default=0)

    class Meta:
        verbose_name = _('assessment attempt')
        verbose_name_plural = _('assessment attempts')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'skill', '-started_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        skill_name = self.skill.name if self.skill else self.assessment.skill.name
        return f"{self.user.username} - {skill_name} - {self.status}"
    
    def calculate_percentage(self):
        """Calculate score percentage"""
        if self.max_score > 0:
            self.percentage = round((self.score / self.max_score) * 100, 2)
        else:
            self.percentage = 0
        return self.percentage
    
    def is_passing(self, passing_threshold=60):
        """Check if user passed (default 60%)"""
        return self.percentage >= passing_threshold


class UserAnswer(models.Model):
    """
    Store user's answer to a specific question.
    NEVER store correct_answer in this model (anti-cheating).
    """
    attempt = models.ForeignKey(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name='user_answers',
        verbose_name=_('attempt')
    )
    
    # Link to QuestionBank instead of Question
    question_bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.CASCADE,
        related_name='user_answers',
        verbose_name=_('question'),
        null=True,  # Nullable for backward compatibility
        blank=True
    )
    
    # Backward compatibility
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='user_answers',
        verbose_name=_('question'),
        null=True,
        blank=True
    )
    
    # User's selected answer (store the OPTION TEXT, not index)
    selected_answer = models.TextField(_('selected answer'))
    
    # Legacy field - database has this as NOT NULL
    user_answer = models.JSONField(_('user answer'), default=dict, blank=True)
    
    # Evaluation (calculated server-side)
    is_correct = models.BooleanField(_('correct'), default=False)
    points_earned = models.FloatField(_('points earned'), default=0)
    
    # Performance tracking
    time_taken_seconds = models.IntegerField(_('time taken (seconds)'), default=0)
    
    # AI evaluation fields
    ai_evaluation = models.TextField(_('AI evaluation'), blank=True, default='')
    requires_manual_review = models.BooleanField(_('requires manual review'), default=False)
    
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('user answer')
        verbose_name_plural = _('user answers')
        ordering = ['attempt', 'answered_at']
        indexes = [
            models.Index(fields=['attempt', 'question_bank']),
        ]

    def __str__(self):
        return f"{self.attempt.user.username} - Q{self.id}"


class UserSkillScore(models.Model):
    """
    User's VERIFIED skill proficiency level (0-10 scale).
    Updated ONLY after completing an assessment.
    This is the SINGLE SOURCE OF TRUTH for gap analysis.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_scores',
        verbose_name=_('user')
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='user_scores',
        verbose_name=_('skill')
    )
    
    # Self-rated level (user's initial claim)
    self_rated_level = models.FloatField(
        _('self-rated level'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="User's self-assessment (0-10)"
    )
    
    # Verified level (from assessment results)
    verified_level = models.FloatField(
        _('verified level'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Verified through assessment (0-10)"
    )
    
    # Status
    STATUS_CHOICES = [
        ('claimed', _('Claimed (Not Verified)')),
        ('verified', _('Verified')),
    ]
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='claimed'
    )
    
    # Assessment history
    last_assessment_attempt = models.ForeignKey(
        AssessmentAttempt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='skill_scores',
        verbose_name=_('last attempt')
    )
    last_assessment_date = models.DateTimeField(null=True, blank=True)
    total_attempts = models.IntegerField(_('total attempts'), default=0)
    best_score_percentage = models.FloatField(_('best score (%)'), default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('user skill score')
        verbose_name_plural = _('user skill scores')
        unique_together = ('user', 'skill')
        ordering = ['-verified_level', 'skill']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['skill', 'verified_level']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.skill.name} - {self.verified_level}/10"
    
    def update_from_attempt(self, attempt):
        """
        Update skill score based on assessment attempt.
        Map percentage (0-100) to proficiency level (0-10).
        """
        self.last_assessment_attempt = attempt
        self.last_assessment_date = attempt.completed_at or timezone.now()
        self.total_attempts += 1
        
        if attempt.percentage > self.best_score_percentage:
            self.best_score_percentage = attempt.percentage
        
        # Map assessment percentage to proficiency level (0-10 scale)
        # 0-59%: Not proficient (0-5.9)
        # 60-69%: Basic proficiency (6.0-6.9)
        # 70-79%: Intermediate proficiency (7.0-7.9)
        # 80-89%: Advanced proficiency (8.0-8.9)
        # 90-100%: Expert proficiency (9.0-10.0)
        self.verified_level = round(attempt.percentage / 10, 1)
        
        # Update status
        if attempt.is_passing():
            self.status = 'verified'
        else:
            self.status = 'claimed'
        
        self.save()
    
    def get_gap(self, required_level):
        """
        Calculate skill gap for a job requirement.
        Returns positive value if gap exists, 0 if qualified.
        """
        gap = required_level - self.verified_level
        return max(gap, 0)
    
    def get_proficiency_display(self):
        """
        Return human-readable proficiency level based on verified_level.
        """
        level = self.verified_level
        if level >= 9.0:
            return 'Expert'
        elif level >= 8.0:
            return 'Advanced'
        elif level >= 7.0:
            return 'Intermediate'
        elif level >= 6.0:
            return 'Basic'
        else:
            return 'Beginner'


# Backward compatibility alias
class UserSkillProfile(UserSkillScore):
    """Alias for UserSkillScore to maintain backward compatibility"""
    class Meta:
        proxy = True
        verbose_name = _('user skill profile')
        verbose_name_plural = _('user skill profiles')
