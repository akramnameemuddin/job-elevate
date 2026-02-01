"""
Debug script to see what's happening in gap analysis
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from recruiter.models import Job, JobSkillRequirement
from assessments.models import UserSkillScore

User = get_user_model()

user = User.objects.first()
job = Job.objects.get(id=5)

print(f"User: {user.email}")
print(f"Job: {job.title}")
print()

# Check job requirements
job_requirements = JobSkillRequirement.objects.filter(job=job).select_related('skill')
print(f"Job Requirements: {job_requirements.count()}")
for req in job_requirements:
    print(f"  - {req.skill.name}: required_proficiency={req.required_proficiency}")
print()

# Check user skill scores
user_scores = UserSkillScore.objects.filter(user=user)
print(f"User Skill Scores: {user_scores.count()}")
for score in user_scores:
    print(f"  - {score.skill.name}: {score.verified_level}/10")
print()

# Manually calculate gaps
print("Calculating Gaps:")
user_skill_scores = {
    score.skill_id: score 
    for score in user_scores.select_related('skill')
}

matched_skills = []
partial_skills = []
all_gaps = []

for requirement in job_requirements:
    skill = requirement.skill
    user_score = user_skill_scores.get(skill.id)
    current_level = user_score.verified_level if user_score else 0
    required_level = requirement.required_proficiency
    
    print(f"\n{skill.name}:")
    print(f"  Current: {current_level}, Required: {required_level}")
    print(f"  Has score: {user_score is not None}")
    print(f"  Meets requirement: {current_level >= required_level}")
    
    gap_value = max(0, required_level - current_level)
    
    if current_level >= required_level:
        matched_skills.append(skill.name)
        print(f"  → MATCHED")
    elif user_score is not None:
        partial_skills.append(skill.name)
        print(f"  → PARTIAL (gap: {gap_value})")
    else:
        all_gaps.append(skill.name)
        print(f"  → MISSING (gap: {gap_value})")

print(f"\n\nSummary:")
print(f"  Matched: {matched_skills}")
print(f"  Partial: {partial_skills}")
print(f"  Missing: {all_gaps}")
print(f"  Total gaps: {len(partial_skills) + len(all_gaps)}")
