"""
Test script to verify complete assessment workflow
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from recruiter.models import Job, JobSkillRequirement
from assessments.models import Skill, QuestionBank, AssessmentAttempt, UserSkillScore

User = get_user_model()

print("=" * 80)
print("ASSESSMENT WORKFLOW TEST")
print("=" * 80)

# Get test data
user = User.objects.first()
job = Job.objects.get(id=5)
skill = Skill.objects.get(name='Python')

print(f"\n1. Test Data:")
print(f"   User: {user.email}")
print(f"   Job: {job.title}")
print(f"   Skill: {skill.name}")

# Check questions exist
questions = QuestionBank.objects.filter(skill=skill)
print(f"\n2. Questions Available: {questions.count()}")
if questions.count() > 0:
    print(f"   ✓ Questions ready for assessment")
else:
    print(f"   ✗ No questions found - need to populate")

# Check job requires this skill
requirement = JobSkillRequirement.objects.filter(job=job, skill=skill).first()
if requirement:
    print(f"\n3. Job Requirement: ✓")
    print(f"   Required Proficiency: {requirement.required_proficiency}/10")
else:
    print(f"\n3. Job Requirement: ✗ Job doesn't require this skill")

# Check user's current skill level
user_score = UserSkillScore.objects.filter(user=user, skill=skill).first()
if user_score:
    print(f"\n4. User Current Level: {user_score.verified_level}/10")
else:
    print(f"\n4. User Current Level: 0/10 (not assessed)")

# Check URLs
print(f"\n5. URL Paths:")
print(f"   Job Detail: /jobs/job/{job.id}/")
print(f"   Gap Analysis: /assessments/job/{job.id}/gaps/")
print(f"   Start Assessment: /assessments/start-from-job/{job.id}/{skill.id}/")
print(f"   Claim & Start: /jobs/job/{job.id}/claim-skill/{skill.id}/")

# Check for in-progress attempts
in_progress = AssessmentAttempt.objects.filter(
    user=user,
    skill=skill,
    status='in_progress'
).count()
print(f"\n6. In-Progress Attempts: {in_progress}")

# Check completed attempts
completed = AssessmentAttempt.objects.filter(
    user=user,
    skill=skill,
    status='completed'
).count()
print(f"   Completed Attempts: {completed}")

print("\n" + "=" * 80)
print("WORKFLOW STATUS:")
print("=" * 80)

all_good = True

if questions.count() < 3:
    print("✗ Need to run: python manage.py add_questions")
    all_good = False
else:
    print("✓ Questions populated")

if not requirement:
    print("✗ Job doesn't require this skill - test with different skill")
    all_good = False
else:
    print("✓ Job requires this skill")

if all_good:
    print("\n✓ READY TO TEST WORKFLOW:")
    print("  1. Navigate to: http://127.0.0.1:8000/jobs/job/5/")
    print("  2. Click 'Add & Take Assessment' or 'Take Assessment' button")
    print("  3. Answer questions")
    print("  4. Submit assessment")
    print("  5. View results")
    print("  6. Return to job detail to see updated match score")
else:
    print("\n✗ SETUP INCOMPLETE - Fix issues above first")

print("=" * 80)
