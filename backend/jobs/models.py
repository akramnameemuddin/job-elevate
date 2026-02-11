from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from recruiter.models import Job

class JobView(models.Model):
    """Model to track which jobs a user has viewed"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_views'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='viewed_by'
    )
    viewed_at = models.DateTimeField(auto_now_add=True)
    view_count = models.IntegerField(default=1)
    
    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.user} viewed {self.job}"

class JobBookmark(models.Model):
    """Model to track bookmarked jobs"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_bookmarks'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='bookmarked_by'
    )
    bookmarked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-bookmarked_at']
    
    def __str__(self):
        return f"{self.user} bookmarked {self.job}"

class UserJobPreference(models.Model):
    """Model to store user job preferences for better recommendations"""
    
    CURRENCY_CHOICES = [
        ('INR', '₹ INR - Indian Rupee'),
        ('USD', '$ USD - US Dollar'),
        ('EUR', '€ EUR - Euro'),
        ('GBP', '£ GBP - British Pound'),
        ('AUD', 'A$ AUD - Australian Dollar'),
        ('CAD', 'C$ CAD - Canadian Dollar'),
        ('SGD', 'S$ SGD - Singapore Dollar'),
        ('AED', 'د.إ AED - UAE Dirham'),
        ('JPY', '¥ JPY - Japanese Yen'),
    ]
    
    SALARY_PERIOD_CHOICES = [
        ('yearly', 'Per Year'),
        ('monthly', 'Per Month'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_preferences'
    )
    preferred_job_types = models.JSONField(_('preferred job types'), default=list)
    preferred_locations = models.JSONField(_('preferred locations'), default=list)
    min_salary_expectation = models.IntegerField(_('minimum salary expectation'), blank=True, null=True)
    max_salary_expectation = models.IntegerField(_('maximum salary expectation'), blank=True, null=True)
    salary_currency = models.CharField(_('salary currency'), max_length=5, choices=CURRENCY_CHOICES, default='INR')
    salary_period = models.CharField(_('salary period'), max_length=10, choices=SALARY_PERIOD_CHOICES, default='yearly')
    remote_preference = models.BooleanField(_('preference for remote work'), default=False)
    industry_preferences = models.JSONField(_('industry preferences'), default=list)
    experience_level = models.CharField(_('experience level'), max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Job preferences for {self.user}"
    
    def get_currency_symbol(self):
        symbols = {
            'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£',
            'AUD': 'A$', 'CAD': 'C$', 'SGD': 'S$', 'AED': 'د.إ', 'JPY': '¥'
        }
        return symbols.get(self.salary_currency, '₹')
    
    def get_primary_location(self):
        """Return the first preferred location or empty string"""
        if self.preferred_locations and len(self.preferred_locations) > 0:
            return self.preferred_locations[0]
        return ''

class JobRecommendation(models.Model):
    """Model to store personalized job recommendations for users"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_recommendations'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='recommended_to'
    )
    score = models.FloatField(_('recommendation score'))
    reason = models.CharField(_('recommendation reason'), max_length=255)
    is_viewed = models.BooleanField(_('recommendation viewed'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-score', '-created_at']
    
    def __str__(self):
        return f"Job {self.job} recommended to {self.user} (score: {self.score})"

class UserSimilarity(models.Model):
    """Model to store similarity between users for collaborative filtering"""
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='similarities_as_user1'
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='similarities_as_user2'
    )
    similarity_score = models.FloatField()
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user1', 'user2')
        ordering = ['-similarity_score']
    
    def __str__(self):
        return f"Similarity between {self.user1} and {self.user2}: {self.similarity_score}"