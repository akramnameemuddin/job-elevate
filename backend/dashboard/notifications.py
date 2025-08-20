"""
Project-wide notification system
Extends the community notification system to work across all apps
"""
from django.contrib.auth import get_user_model
from community.models import Notification
from community.utils import create_notification

User = get_user_model()

class NotificationService:
    """Service class for managing notifications across all apps"""
    
    # Extended notification types for all apps
    NOTIFICATION_TYPES = {
        # Community notifications (existing)
        'like_post': 'Post Liked',
        'like_comment': 'Comment Liked', 
        'comment_post': 'Post Commented',
        'reply_comment': 'Comment Replied',
        'follow_user': 'User Followed',
        'follow_post': 'Post Followed',
        'mention': 'Mentioned',
        
        # Jobs app notifications
        'job_application': 'Job Application Submitted',
        'application_status': 'Application Status Updated',
        'job_recommendation': 'New Job Recommendation',
        'job_posted': 'New Job Posted',
        'job_deadline': 'Job Application Deadline Approaching',
        
        # Learning app notifications
        'course_completed': 'Course Completed',
        'course_recommendation': 'New Course Recommended',
        'skill_assessment': 'Skill Assessment Available',
        'learning_milestone': 'Learning Milestone Achieved',
        
        # Assessment notifications
        'assessment_completed': 'Assessment Completed',
        'assessment_result': 'Assessment Results Available',
        'skill_verified': 'Skill Verified',
        
        # Resume builder notifications
        'resume_generated': 'Resume Generated Successfully',
        'resume_updated': 'Resume Updated',
        'template_suggestion': 'New Resume Template Available',
        
        # Recruiter notifications
        'new_application': 'New Job Application Received',
        'candidate_match': 'Candidate Match Found',
        'profile_viewed': 'Profile Viewed by Candidate',
    }
    
    @staticmethod
    def create_job_notification(recipient, sender, notification_type, message, job=None):
        """Create job-related notification"""
        return create_notification(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            message=message,
            post=None,  # Jobs don't use post field
            comment=None
        )
    
    @staticmethod
    def create_learning_notification(recipient, sender, notification_type, message):
        """Create learning-related notification"""
        return create_notification(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            message=message,
            post=None,
            comment=None
        )
    
    @staticmethod
    def create_assessment_notification(recipient, sender, notification_type, message):
        """Create assessment-related notification"""
        return create_notification(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            message=message,
            post=None,
            comment=None
        )
    
    @staticmethod
    def create_resume_notification(recipient, sender, notification_type, message):
        """Create resume builder notification"""
        return create_notification(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            message=message,
            post=None,
            comment=None
        )
    
    @staticmethod
    def create_recruiter_notification(recipient, sender, notification_type, message):
        """Create recruiter-related notification"""
        return create_notification(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            message=message,
            post=None,
            comment=None
        )
    
    @staticmethod
    def get_user_notifications(user, limit=20):
        """Get all notifications for a user across all apps"""
        return Notification.objects.filter(
            recipient=user
        ).select_related('sender', 'post', 'comment').order_by('-created_at')[:limit]
    
    @staticmethod
    def mark_notifications_read(user, notification_ids=None):
        """Mark notifications as read"""
        queryset = Notification.objects.filter(recipient=user, is_read=False)
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)
        return queryset.update(is_read=True)
    
    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications"""
        return Notification.objects.filter(recipient=user, is_read=False).count()

# Convenience functions for easy import
def notify_job_application(applicant, recruiter, job_title):
    """Notify recruiter of new job application"""
    return NotificationService.create_job_notification(
        recipient=recruiter,
        sender=applicant,
        notification_type='new_application',
        message=f"{applicant.full_name or applicant.username} applied for {job_title}"
    )

def notify_application_status(applicant, recruiter, job_title, status):
    """Notify applicant of application status change"""
    return NotificationService.create_job_notification(
        recipient=applicant,
        sender=recruiter,
        notification_type='application_status',
        message=f"Your application for {job_title} has been {status}"
    )

def notify_job_recommendation(user, job_title, company):
    """Notify user of new job recommendation"""
    return NotificationService.create_job_notification(
        recipient=user,
        sender=user,  # System notification
        notification_type='job_recommendation',
        message=f"New job recommendation: {job_title} at {company}"
    )

def notify_course_completion(user, course_name):
    """Notify user of course completion"""
    return NotificationService.create_learning_notification(
        recipient=user,
        sender=user,  # System notification
        notification_type='course_completed',
        message=f"Congratulations! You completed {course_name}"
    )

def notify_assessment_result(user, assessment_name, score):
    """Notify user of assessment results"""
    return NotificationService.create_assessment_notification(
        recipient=user,
        sender=user,  # System notification
        notification_type='assessment_result',
        message=f"Your {assessment_name} assessment results are ready. Score: {score}%"
    )

def notify_resume_generated(user, resume_name):
    """Notify user of successful resume generation"""
    return NotificationService.create_resume_notification(
        recipient=user,
        sender=user,  # System notification
        notification_type='resume_generated',
        message=f"Your resume '{resume_name}' has been generated successfully"
    )
