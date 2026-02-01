"""
Assessment cooldown management to prevent immediate retests.
"""
from datetime import datetime, timedelta
from django.utils import timezone


class AssessmentCooldownManager:
    """
    Manages cooldown periods between assessment attempts.
    Prevents users from immediately retaking after failure.
    """
    
    # Cooldown period in hours
    COOLDOWN_HOURS = 12
    
    @classmethod
    def check_cooldown(cls, user_id, skill_id):
        """
        Check if user is in cooldown period for a skill.
        
        Returns:
            dict: {
                'in_cooldown': bool,
                'hours_remaining': float (if in cooldown),
                'can_attempt': bool
            }
        """
        from .models import AssessmentAttempt
        
        # Get last attempt for this user and skill
        last_attempt = AssessmentAttempt.objects.filter(
            user_id=user_id,
            skill_id=skill_id,
            status='completed'
        ).order_by('-completed_at').first()
        
        if not last_attempt or not last_attempt.completed_at:
            return {
                'in_cooldown': False,
                'can_attempt': True,
                'hours_remaining': 0
            }
        
        # Check if passed (60% or higher) - no cooldown if passed
        if last_attempt.percentage >= 60:
            return {
                'in_cooldown': False,
                'can_attempt': True,
                'hours_remaining': 0
            }
        
        # Calculate cooldown for failed attempts
        now = timezone.now()
        cooldown_end = last_attempt.completed_at + timedelta(hours=cls.COOLDOWN_HOURS)
        
        if now < cooldown_end:
            hours_remaining = (cooldown_end - now).total_seconds() / 3600
            return {
                'in_cooldown': True,
                'can_attempt': False,
                'hours_remaining': hours_remaining
            }
        
        return {
            'in_cooldown': False,
            'can_attempt': True,
            'hours_remaining': 0
        }
    
    @classmethod
    def get_cooldown_message(cls, user_id, skill_id):
        """Get user-friendly cooldown message"""
        status = cls.check_cooldown(user_id, skill_id)
        
        if status['in_cooldown']:
            hours = int(status['hours_remaining'])
            minutes = int((status['hours_remaining'] - hours) * 60)
            return f"Please wait {hours}h {minutes}m before retaking this assessment."
        
        return None
