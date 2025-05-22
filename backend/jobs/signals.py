from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from accounts.models import User
from recruiter.models import Job, Application
from .models import JobRecommendation, UserSimilarity
from jobs.recommendation_engine import HybridRecommender

logger = logging.getLogger(__name__)
recommender = HybridRecommender()

@receiver(post_save, sender=Application)
def update_recommendations_on_application(sender, instance, created, **kwargs):
    """Update recommendations when a user applies to a job"""
    if created:
        try:
            # Update user similarities for collaborative filtering
            recommender.collaborative_recommender.update_user_similarities(instance.applicant)
        except Exception as e:
            logger.error(f"Error updating recommendations after application: {str(e)}")

@receiver(post_save, sender=User)
def initialize_user_similarities(sender, instance, created, **kwargs):
    """Initialize user similarities when a new user is created"""
    if created and instance.user_type in ['student', 'professional']:
        try:
            # Schedule this for background processing in production
            recommender.collaborative_recommender.update_user_similarities(instance)
        except Exception as e:
            logger.error(f"Error initializing user similarities for new user: {str(e)}")

@receiver(post_save, sender=Job)
def update_recommendations_for_new_job(sender, instance, created, **kwargs):
    """Update recommendations when a new job is posted"""
    if created:
        try:
            # Find potential candidates for this job based on skill match
            candidates = User.objects.filter(user_type__in=['student', 'professional'])
            
            for user in candidates:
                # Calculate match score between user and job
                user_skills = user.get_skills_list()
                job_skills = instance.skills
                
                if not user_skills or not job_skills:
                    continue
                
                # Simple skill matching
                user_skills_set = set([skill.lower().strip() for skill in user_skills])
                job_skills_set = set([skill.lower().strip() for skill in job_skills])
                
                if not user_skills_set or not job_skills_set:
                    continue
                
                # Calculate intersection
                matching_skills = user_skills_set.intersection(job_skills_set)
                match_percentage = len(matching_skills) / len(job_skills_set) if job_skills_set else 0
                
                # If good match, create recommendation
                if match_percentage > 0.5:  # At least 50% match
                    JobRecommendation.objects.create(
                        user=user,
                        job=instance,
                        score=match_percentage,
                        reason="Your skills match this new job posting"
                    )
        except Exception as e:
            logger.error(f"Error updating recommendations for new job: {str(e)}")