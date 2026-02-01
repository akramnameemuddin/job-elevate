"""
Skill-Based Job Matching Engine with Verified Proficiency Tracking

This engine matches users to jobs based on:
1. Verified skill proficiency levels (from assessments)
2. Job skill requirements with minimum thresholds
3. Skill gap analysis and categorization
4. Eligibility status: Eligible / Almost Eligible / Not Eligible
"""

from django.db.models import Q, F, Count, Avg
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SkillBasedJobMatcher:
    """
    Advanced job matching engine that uses verified skill proficiencies.
    
    Eligibility Categories:
    - ELIGIBLE: All required skills meet minimum proficiency thresholds
    - ALMOST_ELIGIBLE: Missing 1-2 skills OR slight gaps in proficiency
    - NOT_ELIGIBLE: Significant skill gaps or missing critical skills
    """
    
    ELIGIBILITY_THRESHOLDS = {
        'eligible': 0.90,          # 90%+ match
        'almost_eligible': 0.70,   # 70-89% match
        'not_eligible': 0.70       # <70% match
    }
    
    def __init__(self, user):
        """
        Initialize matcher for a specific user.
        
        Args:
            user: User instance
        """
        self.user = user
        self.user_skills_cache = None
    
    def get_user_verified_skills(self):
        """
        Get user's verified skill proficiencies (cached).
        
        Returns:
            dict: {skill_id: verified_level}
        """
        if self.user_skills_cache is None:
            from assessments.models import UserSkillProfile
            
            verified_skills = UserSkillProfile.objects.filter(
                user=self.user,
                status='verified'
            ).select_related('skill')
            
            self.user_skills_cache = {
                skill.skill_id: skill.verified_level
                for skill in verified_skills
            }
        
        return self.user_skills_cache
    
    def calculate_job_match(self, job):
        """
        Calculate comprehensive job match score with eligibility categorization.
        
        Args:
            job: Job instance
            
        Returns:
            dict: Complete match analysis including:
                - overall_score: float (0-100)
                - eligibility_status: str (Eligible/Almost Eligible/Not Eligible)
                - matched_skills: list
                - skill_gaps: list
                - weak_skills: list (have skill but below threshold)
                - missing_skills: list (don't have skill)
                - recommendation: str
        """
        from recruiter.models import JobSkillRequirement
        from assessments.models import UserSkillProfile
        
        # Get job requirements
        requirements = JobSkillRequirement.objects.filter(job=job).select_related('skill')
        
        if not requirements.exists():
            # No skill requirements defined - use legacy matching
            return self._legacy_match(job)
        
        # Get user's verified skills
        user_skills = self.get_user_verified_skills()
        
        # Initialize tracking variables
        matched_skills = []
        weak_skills = []
        missing_skills = []
        skill_gaps = []
        
        total_requirements = requirements.count()
        mandatory_requirements = requirements.filter(is_mandatory=True).count()
        
        # Weighted scoring
        total_weight = 0
        earned_weight = 0
        mandatory_met = 0
        
        for req in requirements:
            user_level = user_skills.get(req.skill_id, 0)
            required_level = req.required_proficiency
            gap = max(required_level - user_level, 0)
            
            # Calculate weight for this skill
            skill_weight = req.weight * (1 + req.criticality)  # Higher criticality = more weight
            total_weight += skill_weight
            
            if user_level >= required_level:
                # User meets or exceeds requirement ✓
                earned_weight += skill_weight
                matched_skills.append({
                    'skill_name': req.skill.name,
                    'required': round(required_level, 1),
                    'current': round(user_level, 1),
                    'status': 'qualified',
                    'is_mandatory': req.is_mandatory,
                    'criticality': req.get_criticality_display_text()
                })
                
                if req.is_mandatory:
                    mandatory_met += 1
                    
            elif user_level > 0:
                # User has skill but below threshold
                gap_percentage = (gap / required_level) * 100
                
                # Give partial credit based on proficiency
                earned_weight += skill_weight * (user_level / required_level) * 0.6
                
                weak_skills.append({
                    'skill_name': req.skill.name,
                    'required': round(required_level, 1),
                    'current': round(user_level, 1),
                    'gap': round(gap, 1),
                    'gap_percentage': round(gap_percentage, 1),
                    'status': 'below_threshold',
                    'is_mandatory': req.is_mandatory,
                    'criticality': req.get_criticality_display_text()
                })
                
                skill_gaps.append({
                    'skill_id': req.skill_id,
                    'skill_name': req.skill.name,
                    'gap_value': round(gap, 1),
                    'required_level': round(required_level, 1),
                    'current_level': round(user_level, 1)
                })
                
            else:
                # User doesn't have this skill at all
                missing_skills.append({
                    'skill_name': req.skill.name,
                    'required': round(required_level, 1),
                    'current': 0,
                    'gap': round(required_level, 1),
                    'status': 'missing',
                    'is_mandatory': req.is_mandatory,
                    'criticality': req.get_criticality_display_text()
                })
                
                skill_gaps.append({
                    'skill_id': req.skill_id,
                    'skill_name': req.skill.name,
                    'gap_value': round(required_level, 1),
                    'required_level': round(required_level, 1),
                    'current_level': 0
                })
        
        # Calculate overall score
        if total_weight > 0:
            overall_score = (earned_weight / total_weight) * 100
        else:
            overall_score = 0
        
        # Determine eligibility status
        eligibility_status, readiness_indicator = self._determine_eligibility(
            overall_score,
            mandatory_met,
            mandatory_requirements,
            len(missing_skills),
            len(weak_skills),
            total_requirements
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            eligibility_status,
            overall_score,
            len(matched_skills),
            len(weak_skills),
            len(missing_skills),
            mandatory_met,
            mandatory_requirements
        )
        
        return {
            'job_id': job.id,
            'job_title': job.title,
            'company': job.company,
            'overall_score': round(overall_score, 1),
            'eligibility_status': eligibility_status,
            'readiness_indicator': readiness_indicator,
            'matched_skills': matched_skills,
            'weak_skills': weak_skills,
            'missing_skills': missing_skills,
            'skill_gaps': skill_gaps,
            'summary': {
                'total_requirements': total_requirements,
                'matched_count': len(matched_skills),
                'weak_count': len(weak_skills),
                'missing_count': len(missing_skills),
                'mandatory_met': mandatory_met,
                'mandatory_total': mandatory_requirements
            },
            'recommendation': recommendation,
            'can_apply': eligibility_status in ['Eligible', 'Almost Eligible']
        }
    
    def _determine_eligibility(self, overall_score, mandatory_met, mandatory_total, 
                               missing_count, weak_count, total_requirements):
        """
        Determine job eligibility status based on multiple factors.
        
        Returns:
            tuple: (eligibility_status, readiness_indicator)
        """
        # Check mandatory requirements first
        if mandatory_total > 0 and mandatory_met < mandatory_total:
            return "Not Eligible", "❌ Missing Critical Skills"
        
        # Check overall score thresholds
        if overall_score >= self.ELIGIBILITY_THRESHOLDS['eligible'] * 100:
            return "Eligible", "✅ Fully Qualified"
        
        elif overall_score >= self.ELIGIBILITY_THRESHOLDS['almost_eligible'] * 100:
            # Almost eligible criteria
            if missing_count <= 2 and weak_count <= 3:
                return "Almost Eligible", "⚠️ Minor Gaps - Apply Now"
            else:
                return "Almost Eligible", "⚠️ Some Skill Gaps"
        
        else:
            # Not eligible
            if missing_count >= 5:
                return "Not Eligible", "❌ Significant Gaps"
            elif weak_count >= 4:
                return "Not Eligible", "❌ Below Requirements"
            else:
                return "Not Eligible", "❌ Not Ready Yet"
    
    def _generate_recommendation(self, eligibility_status, overall_score, 
                                 matched_count, weak_count, missing_count,
                                 mandatory_met, mandatory_total):
        """Generate personalized recommendation text."""
        
        if eligibility_status == "Eligible":
            return (f"🎉 Excellent match! You meet all requirements ({matched_count} skills qualified). "
                   f"Apply now with confidence!")
        
        elif eligibility_status == "Almost Eligible":
            if weak_count > 0 and missing_count == 0:
                return (f"💪 Good match! You have all skills but some need improvement. "
                       f"Consider upskilling {weak_count} skill(s) or apply now if confident.")
            elif missing_count <= 2:
                return (f"📚 Close match! You're missing {missing_count} skill(s). "
                       f"Learn these skills to become fully qualified.")
            else:
                return (f"⚡ Fair match. Work on {weak_count + missing_count} skills to improve your chances.")
        
        else:  # Not Eligible
            if mandatory_met < mandatory_total:
                return (f"🚫 Missing critical requirements. Focus on learning mandatory skills first.")
            elif missing_count >= 5:
                return (f"📖 Significant skill gap. Complete learning paths for {missing_count} skills before applying.")
            else:
                return (f"🎯 Build your skills first. Focus on improving {weak_count + missing_count} skills.")
    
    def _legacy_match(self, job):
        """Fallback to legacy skill matching when no requirements are defined."""
        from jobs.recommendation_engine import ContentBasedRecommender
        
        recommender = ContentBasedRecommender()
        user_skills = self.user.get_all_skills_list()
        
        skill_match = recommender.calculate_skill_match(user_skills, job.skills)
        overall_score = skill_match * 100
        
        if overall_score >= 70:
            eligibility = "Eligible"
        elif overall_score >= 50:
            eligibility = "Almost Eligible"
        else:
            eligibility = "Not Eligible"
        
        return {
            'job_id': job.id,
            'job_title': job.title,
            'company': job.company,
            'overall_score': round(overall_score, 1),
            'eligibility_status': eligibility,
            'readiness_indicator': f"Legacy Match: {overall_score:.0f}%",
            'matched_skills': [],
            'weak_skills': [],
            'missing_skills': [],
            'skill_gaps': [],
            'summary': {
                'total_requirements': 0,
                'matched_count': 0,
                'weak_count': 0,
                'missing_count': 0
            },
            'recommendation': f"This job uses legacy matching (no detailed skill requirements defined).",
            'can_apply': overall_score >= 50
        }
    
    def get_recommended_jobs(self, limit=20, eligibility_filter=None):
        """
        Get recommended jobs for user with eligibility categorization.
        
        Args:
            limit: Maximum number of jobs to return
            eligibility_filter: Filter by status ('Eligible', 'Almost Eligible', 'Not Eligible')
            
        Returns:
            list: Job matches sorted by overall_score descending
        """
        from recruiter.models import Job, Application
        
        # Get jobs user hasn't applied to
        applied_job_ids = Application.objects.filter(
            applicant=self.user
        ).values_list('job_id', flat=True)
        
        jobs = Job.objects.filter(
            status='Open'
        ).exclude(
            id__in=applied_job_ids
        ).prefetch_related('skill_requirements__skill')
        
        # Calculate match for each job
        job_matches = []
        for job in jobs:
            match = self.calculate_job_match(job)
            
            # Apply eligibility filter if specified
            if eligibility_filter and match['eligibility_status'] != eligibility_filter:
                continue
            
            job_matches.append(match)
        
        # Sort by overall score descending
        job_matches.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return job_matches[:limit]
    
    def get_skill_gap_summary(self):
        """
        Get summary of all skill gaps across all jobs.
        
        Returns:
            dict: Aggregated skill gap information
        """
        from recruiter.models import Job, JobSkillRequirement
        from assessments.models import UserSkillProfile
        
        # Get all active job requirements
        all_requirements = JobSkillRequirement.objects.filter(
            job__status='Open'
        ).values('skill_id', 'skill__name').annotate(
            avg_required=Avg('required_proficiency'),
            max_required=F('required_proficiency'),
            job_count=Count('job')
        )
        
        user_skills = self.get_user_verified_skills()
        
        gap_summary = []
        for req in all_requirements:
            skill_id = req['skill_id']
            skill_name = req['skill__name']
            avg_required = req['avg_required']
            current_level = user_skills.get(skill_id, 0)
            
            gap = max(avg_required - current_level, 0)
            
            if gap > 0:
                gap_summary.append({
                    'skill_name': skill_name,
                    'current_level': round(current_level, 1),
                    'avg_required': round(avg_required, 1),
                    'gap': round(gap, 1),
                    'job_count': req['job_count'],
                    'priority': 'High' if gap >= 3 else 'Medium' if gap >= 1.5 else 'Low'
                })
        
        # Sort by gap descending
        gap_summary.sort(key=lambda x: x['gap'], reverse=True)
        
        return gap_summary
