import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Count, Q, Avg, F, Case, When, Value, IntegerField, Sum, FloatField
from django.utils import timezone
from datetime import timedelta
from django.contrib.postgres.search import SearchVector, SearchQuery
import json
import logging

from accounts.models import User
from recruiter.models import Job, Application
from .models import JobView, JobBookmark, UserJobPreference, JobRecommendation, UserSimilarity

logger = logging.getLogger(__name__)

class ContentBasedRecommender:
    """Content-based recommendation engine that matches user skills with job requirements"""
    
    def __init__(self):
        pass
    
    def get_skill_vector(self, skills_list):
        """Convert a list of skills to a simple vector representation"""
        # Normalize skills (lowercase, remove extra spaces)
        return [skill.lower().strip() for skill in skills_list if skill.strip()]
    
    def calculate_skill_match(self, user_skills, job_skills):
        """Calculate the skill match score between user and job skills"""
        if not user_skills or not job_skills:
            return 0.0
        
        # Convert to sets for easier intersection calculation
        user_skills_set = set(self.get_skill_vector(user_skills))
        job_skills_set = set(self.get_skill_vector(job_skills))
        
        if not user_skills_set or not job_skills_set:
            return 0.0
        
        # Calculate Jaccard similarity: intersection / union
        intersection = len(user_skills_set.intersection(job_skills_set))
        union = len(user_skills_set.union(job_skills_set))
        
        # Calculate match percentage
        jaccard_similarity = intersection / union if union > 0 else 0.0
        
        # Calculate coverage percentage (how many required job skills the user has)
        coverage = intersection / len(job_skills_set) if job_skills_set else 0.0
        
        # Final score is weighted combination of both metrics
        # Give more weight to coverage of job skills
        score = (0.4 * jaccard_similarity) + (0.6 * coverage)
        
        return score
    
    def calculate_experience_match(self, user_experience, job_experience):
        """Calculate the experience match score between user and job requirements"""
        if user_experience is None or job_experience is None:
            return 0.5  # Neutral score if data is missing
        
        # If user has more experience than required, that's perfect
        if user_experience >= job_experience:
            return 1.0
        
        # If user has less experience, score based on how close they are to the requirement
        if job_experience > 0:
            return user_experience / job_experience
        
        # If job requires no experience, everyone gets a perfect score
        return 1.0
    
    def calculate_location_match(self, preferred_locations, job_location):
        """Calculate location match score using user's preferred locations"""
        if not preferred_locations or not job_location:
            return 0.5  # Neutral score if data is missing

        # Handle remote jobs
        if job_location.lower() in ['remote', 'work from home', 'anywhere']:
            return 1.0  # Remote jobs match all location preferences

        job_loc_lower = job_location.lower()
        best_match = 0.0

        # Check against each preferred location
        for user_location in preferred_locations:
            if not user_location:
                continue

            user_loc_lower = user_location.lower()

            # Check if locations match exactly or if one contains the other
            if user_loc_lower == job_loc_lower:
                return 1.0  # Perfect match found
            elif user_loc_lower in job_loc_lower or job_loc_lower in user_loc_lower:
                best_match = max(best_match, 0.8)
            else:
                # Check if they have at least some common tokens (city/state)
                user_tokens = set(user_loc_lower.split())
                job_tokens = set(job_loc_lower.split())
                common_tokens = user_tokens.intersection(job_tokens)

                if common_tokens:
                    best_match = max(best_match, 0.6)

        return best_match
    
    def calculate_job_type_match(self, user_preferences, job_type):
        """Calculate job type match score based on user preferences"""
        if not user_preferences or not job_type:
            return 0.5  # Neutral score if data is missing

        # Check if job type is in user's preferred job types
        if job_type in user_preferences:
            return 1.0

        # No match but still consider the job
        return 0.2

    def calculate_industry_match(self, preferred_industries, job_description, job_title, company_name):
        """Calculate industry match score based on job content"""
        if not preferred_industries:
            return 0.5  # Neutral score if no preferences

        # Combine job text for analysis
        job_text = f"{job_title} {job_description} {company_name}".lower()

        # Industry keywords mapping
        industry_keywords = {
            'technology': ['tech', 'software', 'developer', 'programming', 'coding', 'it', 'computer', 'digital', 'app', 'web', 'mobile', 'ai', 'machine learning', 'data science'],
            'healthcare': ['health', 'medical', 'hospital', 'clinic', 'nurse', 'doctor', 'patient', 'pharmaceutical', 'biotech', 'medicine'],
            'finance': ['finance', 'bank', 'investment', 'accounting', 'financial', 'money', 'credit', 'loan', 'insurance', 'trading'],
            'education': ['education', 'school', 'university', 'teacher', 'professor', 'student', 'learning', 'academic', 'curriculum'],
            'marketing': ['marketing', 'advertising', 'brand', 'campaign', 'social media', 'content', 'seo', 'digital marketing'],
            'manufacturing': ['factory', 'production', 'assembly', 'industrial', 'machinery', 'automotive'],
            'retail': ['retail', 'store', 'sales', 'customer service', 'merchandise', 'shopping', 'ecommerce'],
            'media': ['media', 'journalism', 'news', 'broadcasting', 'entertainment', 'film', 'television', 'radio'],
            'construction': ['construction', 'building', 'contractor', 'architecture', 'real estate'],
            'transportation': ['transportation', 'logistics', 'shipping', 'delivery', 'trucking', 'airline'],
            'food service': ['restaurant', 'food', 'culinary', 'chef', 'catering', 'hospitality', 'dining']
        }

        best_match = 0.0
        found_any_match = False

        for preferred_industry in preferred_industries:
            industry_lower = preferred_industry.lower()

            # Direct industry name match
            if industry_lower in job_text:
                best_match = max(best_match, 1.0)
                found_any_match = True
                continue

            # Keyword-based matching
            if industry_lower in industry_keywords:
                keywords = industry_keywords[industry_lower]
                matches = sum(1 for keyword in keywords if keyword in job_text)
                if matches > 0:
                    found_any_match = True
                    # Score based on number of keyword matches
                    keyword_score = min(matches / len(keywords) * 2.5, 1.0)
                    # Give at least 0.6 for any keyword match
                    keyword_score = max(keyword_score, 0.6)
                    best_match = max(best_match, keyword_score)

        # If no matches found at all, return low score
        if not found_any_match:
            return 0.2

        return best_match

    def parse_salary_range(self, salary_text):
        """Parse salary text and return minimum and maximum values"""
        if not salary_text:
            return None, None

        try:
            # Clean the salary text
            salary_clean = salary_text.lower().replace('$', '').replace(',', '').replace(' ', '')

            # Handle different formats
            min_salary = None
            max_salary = None

            # Check for range (contains "-" or "to")
            if '-' in salary_clean:
                parts = salary_clean.split('-')
            elif ' to ' in salary_clean:
                parts = salary_clean.split('to')
            else:
                parts = [salary_clean]

            # Parse minimum salary
            if len(parts) >= 1:
                min_part = parts[0].strip()
                # Remove non-numeric characters except decimal point
                min_numeric = ''.join(c for c in min_part if c.isdigit() or c == '.')
                if min_numeric:
                    min_salary = float(min_numeric)
                    # Handle "k" notation
                    if 'k' in min_part:
                        min_salary *= 1000

            # Parse maximum salary
            if len(parts) >= 2:
                max_part = parts[1].strip()
                # Remove non-numeric characters except decimal point
                max_numeric = ''.join(c for c in max_part if c.isdigit() or c == '.')
                if max_numeric:
                    max_salary = float(max_numeric)
                    # Handle "k" notation
                    if 'k' in max_part:
                        max_salary *= 1000
            else:
                max_salary = min_salary  # Single value

            return min_salary, max_salary

        except (ValueError, IndexError, AttributeError):
            return None, None

    def calculate_salary_match(self, user_min_salary, job_salary_text):
        """Calculate salary match score"""
        if not user_min_salary or not job_salary_text:
            return 0.7  # Neutral-positive score if data is missing

        job_min, job_max = self.parse_salary_range(job_salary_text)

        if job_min is None:
            return 0.7  # Neutral-positive if can't parse job salary

        # If job minimum meets or exceeds user's minimum, perfect score
        if job_min >= user_min_salary:
            return 1.0

        # If job maximum meets user's minimum, good score
        if job_max and job_max >= user_min_salary:
            return 0.8

        # If job salary is below user's minimum, calculate how close it is
        if job_max:
            salary_ratio = job_max / user_min_salary
        else:
            salary_ratio = job_min / user_min_salary

        # Score based on how close the salary is to user's expectation
        return min(salary_ratio, 1.0)
    
    def recommend_jobs(self, user, limit=20):
        """Recommend jobs based on enhanced content similarity and user preferences"""
        try:
            # Get user's skills and experience
            user_skills = user.get_skills_list()
            user_experience = user.experience

            # Get user's job preferences if available
            try:
                job_preferences = user.job_preferences
                preferred_job_types = job_preferences.preferred_job_types or []
                preferred_locations = job_preferences.preferred_locations or []
                min_salary = job_preferences.min_salary_expectation
                remote_preference = job_preferences.remote_preference
                industry_preferences = job_preferences.industry_preferences or []
            except UserJobPreference.DoesNotExist:
                preferred_job_types = []
                preferred_locations = []
                min_salary = None
                remote_preference = False
                industry_preferences = []

            # Get IDs of jobs user has already applied to
            applied_job_ids = Application.objects.filter(applicant=user).values_list('job_id', flat=True)

            # Get all active jobs excluding those user has already applied to
            jobs = Job.objects.filter(status='Open').exclude(id__in=applied_job_ids)

            # Calculate scores for each job
            job_scores = []
            for job in jobs:
                # Content-based features
                skill_match = self.calculate_skill_match(user_skills, job.skills)
                exp_match = self.calculate_experience_match(user_experience, job.experience)
                location_match = self.calculate_location_match(preferred_locations, job.location)
                job_type_match = self.calculate_job_type_match(preferred_job_types, job.job_type)
                industry_match = self.calculate_industry_match(
                    industry_preferences,
                    job.description,
                    job.title,
                    job.company
                )
                salary_match = self.calculate_salary_match(min_salary, job.salary)

                # Calculate weighted score with enhanced algorithm
                score = (
                    0.35 * skill_match +      # Skills remain most important
                    0.15 * exp_match +        # Experience
                    0.15 * location_match +   # Location preferences
                    0.15 * job_type_match +   # Job type preferences
                    0.10 * industry_match +   # Industry preferences
                    0.10 * salary_match       # Salary expectations
                )

                # Add remote preference boost
                if remote_preference and (job.job_type == 'Remote' or 'remote' in job.location.lower()):
                    score += 0.05

                # Store the score and enhanced reason
                reason = self._get_enhanced_recommendation_reason(
                    skill_match, exp_match, location_match,
                    job_type_match, industry_match, salary_match
                )
                job_scores.append({
                    'job': job,
                    'score': score,
                    'reason': reason,
                    'match_details': {
                        'skill_match': skill_match,
                        'experience_match': exp_match,
                        'location_match': location_match,
                        'job_type_match': job_type_match,
                        'industry_match': industry_match,
                        'salary_match': salary_match
                    }
                })

            # Sort jobs by score in descending order
            sorted_jobs = sorted(job_scores, key=lambda x: x['score'], reverse=True)

            # Return top N jobs
            return sorted_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error in content-based recommendation for user {user.id}: {str(e)}")
            return []
    
    def _get_recommendation_reason(self, skill_match, exp_match, location_match):
        """Generate a human-readable reason for the recommendation"""
        if skill_match > 0.7:
            return "Your skills match well with this job"
        elif exp_match > 0.8:
            return "You have the right experience for this role"
        elif location_match > 0.8:
            return "This job is in your location"
        else:
            return "This job might interest you"

    def _get_enhanced_recommendation_reason(self, skill_match, exp_match, location_match,
                                          job_type_match, industry_match, salary_match):
        """Generate an enhanced human-readable reason for the recommendation"""
        reasons = []

        # Skill matching
        if skill_match > 0.8:
            reasons.append("Excellent skill match")
        elif skill_match > 0.6:
            reasons.append("Strong skill match")
        elif skill_match > 0.4:
            reasons.append("Good skill match")

        # Experience matching
        if exp_match > 0.9:
            reasons.append("Perfect experience level")
        elif exp_match > 0.7:
            reasons.append("Great experience match")
        elif exp_match > 0.5:
            reasons.append("Good experience fit")

        # Location matching
        if location_match > 0.9:
            reasons.append("Perfect location match")
        elif location_match > 0.7:
            reasons.append("Great location")
        elif location_match > 0.5:
            reasons.append("Good location")

        # Job type matching
        if job_type_match > 0.9:
            reasons.append("Preferred job type")
        elif job_type_match > 0.5:
            reasons.append("Suitable job type")

        # Industry matching
        if industry_match > 0.8:
            reasons.append("Perfect industry match")
        elif industry_match > 0.6:
            reasons.append("Great industry fit")
        elif industry_match > 0.4:
            reasons.append("Good industry match")

        # Salary matching
        if salary_match > 0.9:
            reasons.append("Excellent salary")
        elif salary_match > 0.7:
            reasons.append("Good salary range")

        if not reasons:
            return "Potential opportunity"

        return ", ".join(reasons[:3])  # Limit to top 3 reasons


class CollaborativeRecommender:
    """Collaborative filtering recommendation engine based on user behavior"""
    
    def __init__(self):
        pass
    
    def update_user_similarities(self, user):
        """Update similarity scores between this user and others"""
        try:
            # Get all other users of the same type
            other_users = User.objects.filter(
                user_type=user.user_type
            ).exclude(id=user.id)
            
            # For each other user, calculate similarity
            for other_user in other_users:
                similarity = self._calculate_user_similarity(user, other_user)
                
                # Update or create similarity record
                UserSimilarity.objects.update_or_create(
                    user1=user,
                    user2=other_user,
                    defaults={'similarity_score': similarity}
                )
                
                # Also create the symmetric relationship
                UserSimilarity.objects.update_or_create(
                    user1=other_user,
                    user2=user,
                    defaults={'similarity_score': similarity}
                )
                
        except Exception as e:
            logger.error(f"Error updating user similarities for user {user.id}: {str(e)}")
    
    def _calculate_user_similarity(self, user1, user2):
        """Calculate similarity between two users based on their behavior and profile"""
        try:
            # 1. Calculate similarity based on skill overlap
            user1_skills = set(user1.get_skills_list())
            user2_skills = set(user2.get_skills_list())
            
            # Jaccard similarity for skills
            if user1_skills and user2_skills:
                skill_intersection = len(user1_skills.intersection(user2_skills))
                skill_union = len(user1_skills.union(user2_skills))
                skill_similarity = skill_intersection / skill_union if skill_union > 0 else 0
            else:
                skill_similarity = 0
            
            # 2. Calculate similarity based on job application patterns
            user1_applications = Application.objects.filter(applicant=user1)
            user2_applications = Application.objects.filter(applicant=user2)
            
            user1_applied_jobs = set(user1_applications.values_list('job_id', flat=True))
            user2_applied_jobs = set(user2_applications.values_list('job_id', flat=True))
            
            # Jaccard similarity for applications
            if user1_applied_jobs and user2_applied_jobs:
                job_intersection = len(user1_applied_jobs.intersection(user2_applied_jobs))
                job_union = len(user1_applied_jobs.union(user2_applied_jobs))
                application_similarity = job_intersection / job_union if job_union > 0 else 0
            else:
                application_similarity = 0
            
            # 3. Calculate similarity based on job view patterns
            user1_viewed_jobs = set(JobView.objects.filter(user=user1).values_list('job_id', flat=True))
            user2_viewed_jobs = set(JobView.objects.filter(user=user2).values_list('job_id', flat=True))
            
            # Jaccard similarity for views
            if user1_viewed_jobs and user2_viewed_jobs:
                view_intersection = len(user1_viewed_jobs.intersection(user2_viewed_jobs))
                view_union = len(user1_viewed_jobs.union(user2_viewed_jobs))
                view_similarity = view_intersection / view_union if view_union > 0 else 0
            else:
                view_similarity = 0
            
            # 4. Experience similarity
            if user1.experience is not None and user2.experience is not None:
                # Normalize experience similarity (closer = more similar)
                experience_diff = abs(user1.experience - user2.experience)
                experience_similarity = 1 / (1 + experience_diff)  # Ranges from 0 to 1
            else:
                experience_similarity = 0
            
            # Calculate final similarity score with weights
            final_similarity = (
                0.4 * skill_similarity +
                0.3 * application_similarity +
                0.2 * view_similarity +
                0.1 * experience_similarity
            )
            
            return final_similarity
            
        except Exception as e:
            logger.error(f"Error calculating similarity between users {user1.id} and {user2.id}: {str(e)}")
            return 0
    
    def recommend_jobs(self, user, limit=20):
        """Recommend jobs based on collaborative filtering"""
        try:
            # Get applied job IDs to exclude them
            applied_job_ids = Application.objects.filter(applicant=user).values_list('job_id', flat=True)
            
            # Get similar users (top 10)
            similar_users = UserSimilarity.objects.filter(
                user1=user
            ).order_by('-similarity_score')[:10]
            
            # If no similar users found, return empty list
            if not similar_users:
                return []
                
            # Collect jobs applied to by similar users
            job_scores = {}
            
            for similarity in similar_users:
                similar_user = similarity.user2
                sim_score = similarity.similarity_score
                
                # Skip if similarity is too low
                if sim_score < 0.1:
                    continue
                
                # Get applications from the similar user
                similar_user_applications = Application.objects.filter(
                    applicant=similar_user
                ).exclude(job_id__in=applied_job_ids)
                
                # Get viewed jobs from the similar user
                similar_user_views = JobView.objects.filter(
                    user=similar_user
                ).exclude(job_id__in=applied_job_ids)
                
                # Add applied jobs with higher weight
                for app in similar_user_applications:
                    job_id = app.job_id
                    
                    # Skip jobs the user has already applied to
                    if job_id in applied_job_ids:
                        continue
                        
                    # Check if job is still open
                    try:
                        job = Job.objects.get(id=job_id, status='Open')
                    except Job.DoesNotExist:
                        continue
                    
                    if job_id not in job_scores:
                        job_scores[job_id] = {
                            'job': job,
                            'score': 0,
                            'reason': "Applied to by similar users"
                        }
                    
                    # Weight the score by similarity and the fact it was applied to
                    job_scores[job_id]['score'] += sim_score * 1.5
                
                # Add viewed jobs with lower weight
                for view in similar_user_views:
                    job_id = view.job_id
                    
                    # Skip jobs the user has already applied to
                    if job_id in applied_job_ids:
                        continue
                        
                    # Check if job is still open
                    try:
                        job = Job.objects.get(id=job_id, status='Open')
                    except Job.DoesNotExist:
                        continue
                    
                    if job_id not in job_scores:
                        job_scores[job_id] = {
                            'job': job,
                            'score': 0,
                            'reason': "Viewed by similar users"
                        }
                    
                    # Weight the score by similarity and view count
                    job_scores[job_id]['score'] += sim_score * 0.5 * (1 + 0.1 * view.view_count)
            
            # Convert to list and sort by score
            scored_jobs = list(job_scores.values())
            sorted_jobs = sorted(scored_jobs, key=lambda x: x['score'], reverse=True)
            
            return sorted_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error in collaborative recommendation for user {user.id}: {str(e)}")
            return []


class HybridRecommender:
    """Hybrid recommendation engine that combines content-based and collaborative filtering"""
    
    def __init__(self):
        self.content_recommender = ContentBasedRecommender()
        self.collaborative_recommender = CollaborativeRecommender()
    
    def recommend_jobs(self, user, limit=20):
        """Generate job recommendations using hybrid approach"""
        try:
            # Get recommendations from both systems
            content_recommendations = self.content_recommender.recommend_jobs(user, limit=limit)
            collaborative_recommendations = self.collaborative_recommender.recommend_jobs(user, limit=limit)
            
            # Get applied job IDs to exclude them (safety check)
            applied_job_ids = Application.objects.filter(applicant=user).values_list('job_id', flat=True)
            
            # Combine and deduplicate recommendations
            job_scores = {}
            
            # Add content-based recommendations
            for rec in content_recommendations:
                job = rec['job']
                
                # Skip if job is in applied list
                if job.id in applied_job_ids:
                    continue
                
                job_scores[job.id] = {
                    'job': job,
                    'score': rec['score'] * 0.7,  # Weight for content-based (70%)
                    'reason': rec['reason']
                }
            
            # Add collaborative recommendations
            for rec in collaborative_recommendations:
                job = rec['job']
                
                # Skip if job is in applied list
                if job.id in applied_job_ids:
                    continue
                
                if job.id in job_scores:
                    # If job already exists from content-based, add collaborative score
                    job_scores[job.id]['score'] += rec['score'] * 0.3  # Weight for collaborative (30%)
                    
                    # If collaborative has higher score, use its reason
                    if rec['score'] > (job_scores[job.id]['score'] / 0.7):
                        job_scores[job.id]['reason'] = rec['reason']
                else:
                    # Otherwise add new job with collaborative score
                    job_scores[job.id] = {
                        'job': job,
                        'score': rec['score'] * 0.3,  # Weight for collaborative (30%)
                        'reason': rec['reason']
                    }
            
            # Add popularity boost for jobs with many applicants
            popular_jobs = Job.objects.filter(status='Open').annotate(
                applicant_count=Count('applications')
            ).filter(applicant_count__gt=5)
            
            for job in popular_jobs:
                if job.id in job_scores:
                    # Add small popularity boost
                    job_scores[job.id]['score'] += 0.05
                    
                    # If this job is very popular, change the reason
                    if job.applicant_count > 10 and job_scores[job.id]['reason'] != "Your skills match well with this job":
                        job_scores[job.id]['reason'] = "Popular job with many applicants"
            
            # Convert to list and sort by score
            scored_jobs = list(job_scores.values())
            sorted_jobs = sorted(scored_jobs, key=lambda x: x['score'], reverse=True)
            
            # Save recommendations to database for future reference
            self._save_recommendations(user, sorted_jobs[:limit])
            
            return sorted_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error in hybrid recommendation for user {user.id}: {str(e)}")
            return []
    
    def _save_recommendations(self, user, recommendations):
        """Save recommendations to database for analytics and future use"""
        try:
            # First, delete old recommendations to avoid duplicates
            JobRecommendation.objects.filter(user=user).delete()
            
            # Save new recommendations
            for rec in recommendations:
                JobRecommendation.objects.create(
                    user=user,
                    job=rec['job'],
                    score=rec['score'],
                    reason=rec['reason']
                )
                
        except Exception as e:
            logger.error(f"Error saving recommendations for user {user.id}: {str(e)}")
    
    def track_job_view(self, user, job):
        """Track that a user viewed a job"""
        try:
            # Update or create job view record
            job_view, created = JobView.objects.get_or_create(
                user=user,
                job=job,
                defaults={'view_count': 1}
            )
            
            # If record already existed, increment view count
            if not created:
                job_view.view_count += 1
                job_view.viewed_at = timezone.now()
                job_view.save()
            
            # Mark recommendation as viewed if it exists
            JobRecommendation.objects.filter(user=user, job=job).update(is_viewed=True)
            
            # Update user similarities in background
            # In production, this should be handled by a background task
            self.collaborative_recommender.update_user_similarities(user)
            
        except Exception as e:
            logger.error(f"Error tracking job view for user {user.id}, job {job.id}: {str(e)}")
    
    def track_job_bookmark(self, user, job):
        """Track that a user bookmarked a job"""
        try:
            # Create job bookmark record (if not exists)
            JobBookmark.objects.get_or_create(user=user, job=job)
            
            # Update user similarities in background
            # In production, this should be handled by a background task
            self.collaborative_recommender.update_user_similarities(user)
            
        except Exception as e:
            logger.error(f"Error tracking job bookmark for user {user.id}, job {job.id}: {str(e)}")
    
    def track_job_application(self, user, job):
        """Track that a user applied to a job"""
        try:
            # We don't need to create any records here as the Application model already exists
            # However, we should update user similarities
            self.collaborative_recommender.update_user_similarities(user)
            
        except Exception as e:
            logger.error(f"Error tracking job application for user {user.id}, job {job.id}: {str(e)}")