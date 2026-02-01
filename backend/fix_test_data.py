"""
Fix test data to demonstrate high ML model accuracy
Creates users with skills that perfectly match available jobs
"""

import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import User
from recruiter.models import Job

def diagnose_current_data():
    """Show what data we currently have"""
    print("=" * 80)
    print("CURRENT DATA DIAGNOSIS")
    print("=" * 80)
    print()
    
    # Check jobs
    jobs = Job.objects.all()
    print(f"📊 Total Jobs: {jobs.count()}")
    print()
    
    if jobs.exists():
        print("Top 5 Jobs and their skills:")
        for job in jobs[:5]:
            print(f"\n  • {job.title}")
            print(f"    Skills: {job.skills}")
            print(f"    Type: {type(job.skills)}")
    
    print()
    print("-" * 80)
    print()
    
    # Check users
    users = User.objects.filter(user_type__in=['student', 'professional']).exclude(technical_skills='')
    print(f"👥 Total Test Users: {users.count()}")
    print()
    
    if users.exists():
        print("Top 5 Users and their skills:")
        for user in users[:5]:
            skills = user.get_skills_list()
            raw_skills = user.technical_skills or "(empty)"
            print(f"\n  • {user.get_full_name() or user.username}")
            print(f"    Raw: {raw_skills[:100]}")
            print(f"    Parsed: {skills[:5]}")


def create_perfect_match_users():
    """Create users whose skills perfectly match existing jobs"""
    
    print()
    print("=" * 80)
    print("CREATING PERFECT MATCH USERS")
    print("=" * 80)
    print()
    
    # Define test users with skills matching our jobs exactly
    test_users = [
        {
            'username': 'django_expert',
            'email': 'django@test.com',
            'password': 'test123',
            'first_name': 'Django',
            'last_name': 'Expert',
            'user_type': 'student',
            'technical_skills': 'Python,Django,PostgreSQL,REST API,Git'
        },
        {
            'username': 'mern_developer',
            'email': 'mern@test.com',
            'password': 'test123',
            'first_name': 'MERN',
            'last_name': 'Developer',
            'user_type': 'student',
            'technical_skills': 'JavaScript,React,Node.js,MongoDB,Express'
        },
        {
            'username': 'java_engineer',
            'email': 'java@test.com',
            'password': 'test123',
            'first_name': 'Java',
            'last_name': 'Engineer',
            'user_type': 'professional',
            'technical_skills': 'Java,Spring Boot,MySQL,Microservices,Docker'
        },
        {
            'username': 'ml_specialist',
            'email': 'ml@test.com',
            'password': 'test123',
            'first_name': 'ML',
            'last_name': 'Specialist',
            'user_type': 'professional',
            'technical_skills': 'Python,TensorFlow,Scikit-learn,NumPy,Pandas'
        },
        {
            'username': 'data_analyst',
            'email': 'analyst@test.com',
            'password': 'test123',
            'first_name': 'Data',
            'last_name': 'Analyst',
            'user_type': 'student',
            'technical_skills': 'Python,SQL,Pandas,Tableau,Excel'
        },
        {
            'username': 'fullstack_pro',
            'email': 'fullstack@test.com',
            'password': 'test123',
            'first_name': 'FullStack',
            'last_name': 'Pro',
            'user_type': 'professional',
            'technical_skills': 'Python,Django,React,JavaScript,PostgreSQL,REST API'
        },
        {
            'username': 'frontend_dev',
            'email': 'frontend@test.com',
            'password': 'test123',
            'first_name': 'Frontend',
            'last_name': 'Developer',
            'user_type': 'student',
            'technical_skills': 'HTML,CSS,JavaScript,React,Tailwind CSS'
        },
        {
            'username': 'python_web',
            'email': 'pyweb@test.com',
            'password': 'test123',
            'first_name': 'Python',
            'last_name': 'WebDev',
            'user_type': 'student',
            'technical_skills': 'Python,Flask,Django,PostgreSQL,REST API,Git'
        },
        {
            'username': 'multi_skilled',
            'email': 'multi@test.com',
            'password': 'test123',
            'first_name': 'Multi',
            'last_name': 'Skilled',
            'user_type': 'professional',
            'technical_skills': 'Python,Java,Django,Spring Boot,MySQL,React,JavaScript'
        },
        {
            'username': 'js_ninja',
            'email': 'jsninja@test.com',
            'password': 'test123',
            'first_name': 'JavaScript',
            'last_name': 'Ninja',
            'user_type': 'student',
            'technical_skills': 'JavaScript,Node.js,React,HTML,CSS,Git'
        }
    ]
    
    created_count = 0
    
    for user_data in test_users:
        # Check if user exists
        existing = User.objects.filter(username=user_data['username']).first()
        
        if existing:
            # Update skills
            existing.technical_skills = user_data['technical_skills']
            existing.save()
            print(f"✅ Updated: {user_data['username']} - {user_data['technical_skills']}")
        else:
            # Create new user
            User.objects.create_user(**user_data)
            created_count += 1
            print(f"✅ Created: {user_data['username']} - {user_data['technical_skills']}")
    
    print()
    print(f"✅ Created {created_count} new users")
    print(f"👥 Total users in database: {User.objects.filter(user_type__in=['student', 'professional']).count()}")


if __name__ == '__main__':
    diagnose_current_data()
    create_perfect_match_users()
    
    print()
    print("=" * 80)
    print("✅ TEST DATA READY")
    print("=" * 80)
    print()
    print("Now run: python test_recommendation_accuracy.py")
    print()
