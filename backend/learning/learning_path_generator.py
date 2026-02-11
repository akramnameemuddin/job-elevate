"""
AI-Powered Personalized Learning Path Generator

Analyzes assessment results, identifies weak areas, and generates
custom learning paths to help users bridge skill gaps and qualify for jobs.

Uses AI to:
1. Analyze assessment weak points
2. Recommend targeted learning resources
3. Create timeline-based study plans
4. Generate motivational content
"""

from django.utils import timezone
from django.conf import settings
from typing import Dict, List, Optional
import logging
from google import genai
from google.genai import types
import json
import os

logger = logging.getLogger(__name__)


class LearningPathGenerator:
    """
    Generate personalized learning paths using AI.
    
    Features:
    - AI-powered skill gap analysis
    - Customized course recommendations
    - Timeline-based learning plans
    - Motivational content generation
    """
    
    # Learning time estimates per proficiency point
    HOURS_PER_PROFICIENCY_POINT = {
        'basic': 8,         # 8 hours to gain 1 point in basic level
        'intermediate': 12,  # 12 hours per point in intermediate
        'advanced': 20       # 20 hours per point in advanced
    }
    
    @classmethod
    def generate_personalized_path(cls, user, skill, current_level, target_level=6.0):
        """
        Generate AI-powered personalized learning path.
        
        Args:
            user: User instance
            skill: Skill instance
            current_level: Current proficiency (0-10)
            target_level: Target proficiency (0-10)
            
        Returns:
            LearningPath instance
        """
        from learning.models import LearningPath, SkillGap, Course, LearningPathCourse
        
        gap_value = target_level - current_level
        
        # Create skill gap
        skill_gap, created = SkillGap.objects.get_or_create(
            user=user,
            skill=skill,
            target_job_title=f"General {skill.name} Position",
            defaults={
                'current_level': current_level,
                'required_level': target_level,
                'gap_value': gap_value,
                'gap_severity': gap_value / target_level if target_level > 0 else 0,
                'priority': 'high' if gap_value > 3 else 'moderate'
            }
        )
        
        # Use AI to generate learning recommendations
        api_key = getattr(settings, 'GOOGLE_API_KEY', os.environ.get('GOOGLE_API_KEY'))

        # Check circuit breaker before calling Gemini
        try:
            from agents.circuit_breaker import is_open as _cb_open, record_error as _cb_record
            _breaker_available = True
        except ImportError:
            _breaker_available = False

        if api_key and not (_breaker_available and _cb_open()):
            try:
                client = genai.Client(api_key=api_key)
                
                prompt = f"""Generate a personalized learning plan for improving {skill.name} skills.

Current Level: {current_level}/10
Target Level: {target_level}/10
Gap: {gap_value} points

Provide a JSON response with:
1. Learning path title
2. Motivational description
3. Key focus areas (3-5 topics)
4. Recommended learning order
5. Study tips

JSON format:
{{
    "title": "Path to {skill.name} Mastery",
    "description": "Motivational description here...",
    "focus_areas": ["Topic 1", "Topic 2", "Topic 3"],
    "learning_order": ["Step 1", "Step 2", "Step 3"],
    "study_tips": ["Tip 1", "Tip 2", "Tip 3"],
    "estimated_weeks": 8
}}"""
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash-lite',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=2048
                    )
                )
                
                content = response.text.strip()
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0].strip()
                elif content.startswith('```'):
                    content = content.split('```')[1].split('```')[0].strip()
                
                ai_data = json.loads(content)
                
            except Exception as e:
                logger.warning(f"AI generation failed: {e}")
                if _breaker_available:
                    _cb_record(e)
                ai_data = cls._fallback_learning_data(skill.name, current_level, target_level)
        else:
            ai_data = cls._fallback_learning_data(skill.name, current_level, target_level)
        
        # Create learning path
        learning_path, created = LearningPath.objects.get_or_create(
            user=user,
            skill_gap=skill_gap,
            defaults={
                'title': ai_data.get('title', f"Path to {skill.name} Mastery"),
                'description': ai_data.get('description', f"Improve your {skill.name} skills"),
                'estimated_weeks': ai_data.get('estimated_weeks', 8),
                'estimated_hours': int(gap_value * 15),
                'status': 'not_started'
            }
        )
        
        # Find and add relevant courses
        courses = Course.objects.filter(
            skill=skill,
            is_active=True
        ).order_by('difficulty_level', '-rating')
        
        # Add courses based on current level
        order = 1
        if current_level < 3:
            # Add beginner courses
            for course in courses.filter(difficulty_level='beginner')[:2]:
                LearningPathCourse.objects.get_or_create(
                    learning_path=learning_path,
                    course=course,
                    defaults={'order': order}
                )
                order += 1
        
        if current_level < 6:
            # Add intermediate courses
            for course in courses.filter(difficulty_level='intermediate')[:2]:
                LearningPathCourse.objects.get_or_create(
                    learning_path=learning_path,
                    course=course,
                    defaults={'order': order}
                )
                order += 1
        
        if target_level >= 7:
            # Add advanced courses
            for course in courses.filter(difficulty_level='advanced')[:2]:
                LearningPathCourse.objects.get_or_create(
                    learning_path=learning_path,
                    course=course,
                    defaults={'order': order}
                )
                order += 1
        
        return learning_path
    
    @classmethod
    def _fallback_learning_data(cls, skill_name, current_level, target_level):
        """Fallback learning data when AI is unavailable."""
        gap = target_level - current_level
        
        return {
            'title': f"Path to {skill_name} Mastery",
            'description': (
                f"Comprehensive learning path to improve your {skill_name} proficiency "
                f"from {current_level:.1f}/10 to {target_level:.1f}/10. "
                f"Complete the courses in order, practice regularly, and retake the assessment."
            ),
            'focus_areas': [
                f"Fundamental {skill_name} concepts",
                f"Practical {skill_name} applications",
                f"Advanced {skill_name} techniques"
            ],
            'learning_order': [
                "Start with foundational courses",
                "Practice with real projects",
                "Review and reinforce weak areas",
                "Take practice assessments"
            ],
            'study_tips': [
                "Set aside dedicated study time each day",
                "Apply concepts through hands-on projects",
                "Join online communities for support",
                "Track your progress regularly"
            ],
            'estimated_weeks': max(int(gap * 2), 4)
        }


# Maintain backward compatibility
class PersonalizedLearningPathGenerator:
    
    def generate_from_assessment(self, assessment_attempt, target_proficiency=8.0):
        """
        Generate learning path based on assessment performance.
        Analyzes which levels (basic/intermediate/advanced) need improvement.
        
        Args:
            assessment_attempt: AssessmentAttempt instance
            target_proficiency: Desired proficiency level (0-10)
            
        Returns:
            dict: Learning path with topics, resources, and timeline
        """
        from assessments.models import UserSkillProfile
        from assessments.skill_intelligence_engine import SkillAssessmentGenerator
        
        # Calculate weighted scores
        score_breakdown = SkillAssessmentGenerator.calculate_weighted_proficiency(assessment_attempt)
        
        skill = assessment_attempt.assessment.skill
        current_proficiency = score_breakdown['verified_proficiency']
        
        # Identify weak areas
        weak_areas = []
        if score_breakdown['basic_score'] < 70:
            weak_areas.append({
                'level': 'basic',
                'current_score': score_breakdown['basic_score'],
                'target_score': 80,
                'priority': 'Critical',
                'topics': self._get_basic_topics(skill)
            })
        
        if score_breakdown['intermediate_score'] < 70:
            weak_areas.append({
                'level': 'intermediate',
                'current_score': score_breakdown['intermediate_score'],
                'target_score': 80,
                'priority': 'High',
                'topics': self._get_intermediate_topics(skill)
            })
        
        if score_breakdown['advanced_score'] < 70:
            weak_areas.append({
                'level': 'advanced',
                'current_score': score_breakdown['advanced_score'],
                'target_score': 80,
                'priority': 'Medium',
                'topics': self._get_advanced_topics(skill)
            })
        
        # Get or create skill gap
        from learning.models import SkillGap, LearningPath
        
        skill_gap, created = SkillGap.objects.get_or_create(
            user=self.user,
            skill=skill,
            target_job_title=f"General {skill.name} Role",
            defaults={
                'current_level': current_proficiency,
                'required_level': target_proficiency,
                'job_criticality': 0.7
            }
        )
        
        # Update gap values
        skill_gap.current_level = current_proficiency
        skill_gap.required_level = target_proficiency
        skill_gap.save()
        
        # Generate learning path
        learning_path = self._create_learning_path(
            skill_gap=skill_gap,
            weak_areas=weak_areas,
            current_proficiency=current_proficiency,
            target_proficiency=target_proficiency
        )
        
        return learning_path
    
    def generate_for_job(self, job, create_paths=True):
        """
        Generate learning paths for all skill gaps relative to a target job.
        
        Args:
            job: Job instance
            create_paths: Whether to create LearningPath records in DB
            
        Returns:
            list: Learning paths for each skill gap
        """
        from recruiter.models import JobSkillRequirement
        from assessments.models import UserSkillProfile
        from learning.models import SkillGap
        
        # Get job requirements
        requirements = JobSkillRequirement.objects.filter(job=job).select_related('skill')
        
        # Get user's current skill levels
        user_skills = UserSkillProfile.objects.filter(
            user=self.user,
            status='verified'
        ).select_related('skill')
        
        user_skill_dict = {us.skill_id: us.verified_level for us in user_skills}
        
        learning_paths = []
        
        for req in requirements:
            current_level = user_skill_dict.get(req.skill_id, 0)
            required_level = req.required_proficiency
            
            # Only create path if there's a gap
            if current_level < required_level:
                # Create or update skill gap
                skill_gap, created = SkillGap.objects.update_or_create(
                    user=self.user,
                    skill=req.skill,
                    target_job_title=job.title,
                    defaults={
                        'current_level': current_level,
                        'required_level': required_level,
                        'job_criticality': req.criticality,
                        'related_job': job,
                        'is_addressed': False
                    }
                )
                
                # Generate learning path
                if create_paths:
                    path = self._create_learning_path_for_job_skill(
                        skill_gap=skill_gap,
                        requirement=req,
                        current_level=current_level
                    )
                    learning_paths.append(path)
        
        return learning_paths
    
    def _create_learning_path(self, skill_gap, weak_areas, current_proficiency, target_proficiency):
        """Create comprehensive learning path."""
        from learning.models import LearningPath, Course, LearningPathCourse
        
        gap_value = target_proficiency - current_proficiency
        
        # Generate learning path title
        title = f"Path to {skill_gap.skill.name} Mastery (Level {target_proficiency:.1f})"
        
        description = self._generate_path_description(
            skill_gap.skill.name,
            current_proficiency,
            target_proficiency,
            weak_areas
        )
        
        # Estimate total hours
        total_hours = self._estimate_learning_hours(gap_value, weak_areas)
        total_weeks = max(int(total_hours / 10), 2)  # Assuming 10 hours/week
        
        # Create or get learning path
        learning_path, created = LearningPath.objects.get_or_create(
            user=self.user,
            skill_gap=skill_gap,
            defaults={
                'title': title,
                'description': description,
                'estimated_hours': total_hours,
                'estimated_weeks': total_weeks,
                'status': 'not_started'
            }
        )
        
        if not created:
            # Update existing path
            learning_path.description = description
            learning_path.estimated_hours = total_hours
            learning_path.estimated_weeks = total_weeks
            learning_path.save()
        
        # Find and add relevant courses
        courses = Course.objects.filter(
            skill=skill_gap.skill,
            is_active=True
        ).order_by('difficulty_level', '-rating')
        
        # Add courses to path based on weak areas
        order = 1
        for weak_area in weak_areas:
            level = weak_area['level']
            
            # Map levels to difficulty
            difficulty_map = {
                'basic': 'beginner',
                'intermediate': 'intermediate',
                'advanced': 'advanced'
            }
            
            difficulty = difficulty_map[level]
            
            # Get courses for this difficulty
            level_courses = courses.filter(difficulty_level=difficulty)[:2]  # Top 2 courses per level
            
            for course in level_courses:
                LearningPathCourse.objects.get_or_create(
                    learning_path=learning_path,
                    course=course,
                    defaults={'order': order}
                )
                order += 1
        
        return {
            'learning_path_id': learning_path.id,
            'title': learning_path.title,
            'description': learning_path.description,
            'skill': skill_gap.skill.name,
            'current_level': round(current_proficiency, 1),
            'target_level': round(target_proficiency, 1),
            'gap': round(gap_value, 1),
            'weak_areas': weak_areas,
            'estimated_hours': total_hours,
            'estimated_weeks': total_weeks,
            'course_count': learning_path.courses.count(),
            'status': learning_path.status,
            'message': 'Learning path created successfully. Start learning to improve your proficiency!'
        }
    
    def _create_learning_path_for_job_skill(self, skill_gap, requirement, current_level):
        """Create learning path for a specific job skill requirement."""
        from learning.models import LearningPath, Course, LearningPathCourse
        
        required_level = requirement.required_proficiency
        gap_value = required_level - current_level
        
        # Determine which levels need work based on gap
        weak_areas = []
        
        if current_level < 3:
            # Need basic level work
            weak_areas.append({
                'level': 'basic',
                'current_score': current_level * 10,
                'target_score': min(required_level * 10, 80),
                'priority': 'Critical',
                'topics': self._get_basic_topics(skill_gap.skill)
            })
        
        if current_level < 6 and required_level >= 5:
            # Need intermediate level work
            weak_areas.append({
                'level': 'intermediate',
                'current_score': current_level * 10,
                'target_score': min(required_level * 10, 80),
                'priority': 'High',
                'topics': self._get_intermediate_topics(skill_gap.skill)
            })
        
        if required_level >= 7:
            # Need advanced level work
            weak_areas.append({
                'level': 'advanced',
                'current_score': current_level * 10,
                'target_score': required_level * 10,
                'priority': 'Medium',
                'topics': self._get_advanced_topics(skill_gap.skill)
            })
        
        return self._create_learning_path(
            skill_gap=skill_gap,
            weak_areas=weak_areas,
            current_proficiency=current_level,
            target_proficiency=required_level
        )
    
    def _generate_path_description(self, skill_name, current, target, weak_areas):
        """Generate descriptive text for learning path."""
        gap = target - current
        
        description = (
            f"Comprehensive learning path to improve your {skill_name} proficiency "
            f"from {current:.1f}/10 to {target:.1f}/10 (gap: {gap:.1f} points).\n\n"
        )
        
        if weak_areas:
            description += "**Focus Areas:**\n"
            for area in weak_areas:
                level = area['level'].capitalize()
                score = area['current_score']
                priority = area['priority']
                description += f"- {level} Level (Current: {score:.0f}%, Priority: {priority})\n"
        
        description += "\nComplete the courses in order, practice regularly, and retake the assessment to verify improvement."
        
        return description
    
    def _estimate_learning_hours(self, gap_value, weak_areas):
        """Estimate total learning hours needed."""
        total_hours = 0
        
        for area in weak_areas:
            level = area['level']
            score_gap = (area['target_score'] - area['current_score']) / 100  # Normalize to 0-1
            
            # Use level-specific hour estimates
            hours_per_point = self.HOURS_PER_PROFICIENCY_POINT[level]
            total_hours += score_gap * hours_per_point * gap_value
        
        # Minimum 10 hours, maximum 200 hours
        return max(min(int(total_hours), 200), 10)
    
    def _get_basic_topics(self, skill):
        """Get foundational topics for a skill."""
        # This would ideally be AI-generated or pulled from a knowledge base
        return [
            f"Introduction to {skill.name}",
            f"Core {skill.name} concepts",
            f"Basic {skill.name} syntax and structure",
            f"Simple {skill.name} examples and exercises"
        ]
    
    def _get_intermediate_topics(self, skill):
        """Get intermediate topics for a skill."""
        return [
            f"Applied {skill.name} techniques",
            f"Real-world {skill.name} problems",
            f"{skill.name} best practices",
            f"Intermediate {skill.name} projects"
        ]
    
    def _get_advanced_topics(self, skill):
        """Get advanced topics for a skill."""
        return [
            f"Advanced {skill.name} patterns",
            f"{skill.name} optimization and performance",
            f"Complex {skill.name} architectures",
            f"Expert-level {skill.name} challenges"
        ]
    
    def get_all_learning_paths(self, status=None):
        """
        Get all learning paths for user.
        
        Args:
            status: Filter by status (not_started, in_progress, completed, paused)
            
        Returns:
            QuerySet: LearningPath instances
        """
        from learning.models import LearningPath
        
        paths = LearningPath.objects.filter(
            user=self.user
        ).select_related('skill_gap__skill').prefetch_related('courses')
        
        if status:
            paths = paths.filter(status=status)
        
        return paths.order_by('-created_at')
