"""
Helper functions for job detail view to integrate skill gap analysis
"""
from assessments.models import UserSkillScore
from recruiter.models import JobSkillRequirement


def calculate_skill_gap_analysis(job, user):
    """
    Calculate skill gap analysis for a user against job requirements.
    
    Returns dict with:
    - skill_requirements: All required skills
    - verified_skills: Skills where user meets requirement
    - partial_skills: Skills where user has some proficiency but gap exists
    - missing_skills: Skills user hasn't assessed yet
    - match_score: Overall match percentage (0-100)
    - can_apply: Whether user can apply (all mandatory skills met)
    """
    # Get job skill requirements
    skill_requirements = JobSkillRequirement.objects.filter(
        job=job
    ).select_related('skill', 'skill__category').order_by('-criticality', '-required_proficiency')
    
    # Get user's verified skill scores
    user_scores = UserSkillScore.objects.filter(
        user=user,
        status='verified'
    ).select_related('skill')
    
    user_scores_dict = {score.skill_id: score for score in user_scores}
    
    # Categorize skills
    verified_skills = []
    partial_skills = []
    missing_skills = []
    
    total_points = 0
    earned_points = 0
    mandatory_requirements = 0
    mandatory_met = 0
    
    for req in skill_requirements:
        skill_data = {
            'skill': req.skill,
            'skill_id': req.skill.id,
            'required_proficiency': req.required_proficiency,
            'criticality': req.get_criticality_display_text(),
            'is_mandatory': req.is_mandatory,
            'weight': req.weight,
        }
        
        # Calculate points based on weight
        points_for_skill = req.weight * 10
        total_points += points_for_skill
        
        if req.is_mandatory:
            mandatory_requirements += 1
        
        # Check user's proficiency
        user_score = user_scores_dict.get(req.skill_id)
        
        if user_score:
            user_proficiency = user_score.verified_level
            skill_data['user_proficiency'] = user_proficiency
            skill_data['gap'] = max(req.required_proficiency - user_proficiency, 0)
            skill_data['is_claimed'] = True
            
            # Categorize
            if user_proficiency >= req.required_proficiency:
                # User meets requirement
                verified_skills.append(skill_data)
                earned_points += points_for_skill
                if req.is_mandatory:
                    mandatory_met += 1
            else:
                # User has partial proficiency
                partial_skills.append(skill_data)
                # Award partial points based on how close they are
                gap = req.required_proficiency - user_proficiency
                partial_ratio = max(1 - (gap / req.required_proficiency), 0)
                earned_points += points_for_skill * partial_ratio
        else:
            # User hasn't assessed this skill
            skill_data['user_proficiency'] = 0
            skill_data['gap'] = req.required_proficiency
            skill_data['is_claimed'] = False
            missing_skills.append(skill_data)
    
    # Calculate match score
    if total_points > 0:
        match_score = int((earned_points / total_points) * 100)
    else:
        match_score = 0
    
    # Determine if user can apply
    # Can apply if all mandatory requirements are met AND overall score >= 50%
    can_apply = (mandatory_met >= mandatory_requirements) and (match_score >= 50)
    
    return {
        'skill_requirements': skill_requirements,
        'verified_skills': verified_skills,
        'partial_skills': partial_skills,
        'missing_skills': missing_skills,
        'match_score': match_score,
        'can_apply': can_apply,
        'mandatory_met': mandatory_met,
        'mandatory_total': mandatory_requirements,
    }
