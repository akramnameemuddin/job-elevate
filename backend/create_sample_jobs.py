"""
Create sample jobs for ML model testing
"""

import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from recruiter.models import Job
from accounts.models import User

def create_sample_jobs():
    """Create diverse sample jobs for testing recommendation engine"""
    
    print("Creating sample jobs for ML testing...")
    
    # Get or create a recruiter user
    recruiter = User.objects.filter(user_type='recruiter').first()
    
    if not recruiter:
        print("No recruiter found. Creating sample recruiter...")
        recruiter = User.objects.create_user(
            username='test_recruiter',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter',
            first_name='Test',
            last_name='Recruiter'
        )
    
    sample_jobs = [
        {
            'title': 'Python Django Developer',
            'company': 'Tech Solutions Inc',
            'location': 'Bangalore, India',
            'job_type': 'Full-time',
            'experience': 2,
            'salary': '8-12 LPA',
            'description': 'Looking for Django developer to build scalable web applications',
            'skills': ['Python', 'Django', 'PostgreSQL', 'REST API', 'Git'],  # JSON list
            'status': 'Open'
        },
        {
            'title': 'Full Stack Developer (MERN)',
            'company': 'Startup Hub',
            'location': 'Hyderabad, India',
            'job_type': 'Full-time',
            'experience': 3,
            'salary': '10-15 LPA',
            'description': 'Build modern web applications using MERN stack',
            'skills': ['JavaScript', 'React', 'Node.js', 'MongoDB', 'Express'],
            'status': 'Open'
        },
        {
            'title': 'Java Backend Engineer',
            'company': 'Enterprise Corp',
            'location': 'Mumbai, India',
            'job_type': 'Full-time',
            'experience': 4,
            'salary': '12-18 LPA',
            'description': 'Develop microservices using Spring Boot',
            'skills': ['Java', 'Spring Boot', 'MySQL', 'Microservices', 'Docker'],
            'status': 'Open'
        },
        {
            'title': 'Machine Learning Engineer',
            'company': 'AI Labs',
            'location': 'Pune, India',
            'job_type': 'Full-time',
            'experience': 3,
            'salary': '15-20 LPA',
            'description': 'Build ML models for production systems',
            'skills': ['Python', 'TensorFlow', 'Scikit-learn', 'NumPy', 'Pandas'],
            'status': 'Open'
        },
        {
            'title': 'DevOps Engineer',
            'company': 'Cloud Services Ltd',
            'location': 'Chennai, India',
            'job_type': 'Full-time',
            'experience': 3,
            'salary': '12-16 LPA',
            'description': 'Manage cloud infrastructure and CI/CD pipelines',
            'skills': ['AWS', 'Docker', 'Kubernetes', 'Jenkins', 'Terraform'],
            'status': 'Open'
        },
        {
            'title': 'Data Analyst',
            'company': 'Analytics Pro',
            'location': 'Delhi, India',
            'job_type': 'Full-time',
            'experience': 2,
            'salary': '7-10 LPA',
            'description': 'Analyze data and create insights using Python and SQL',
            'skills': ['Python', 'SQL', 'Pandas', 'Tableau', 'Excel'],
            'status': 'Open'
        },
        {
            'title': 'React Native Developer',
            'company': 'Mobile First Inc',
            'location': 'Remote',
            'job_type': 'Full-time',
            'experience': 2,
            'salary': '8-14 LPA',
            'description': 'Build cross-platform mobile applications',
            'skills': ['JavaScript', 'React Native', 'Redux', 'Firebase'],
            'status': 'Open'
        },
        {
            'title': 'Frontend Developer',
            'company': 'UI Masters',
            'location': 'Bangalore, India',
            'job_type': 'Full-time',
            'experience': 1,
            'salary': '5-8 LPA',
            'description': 'Create beautiful user interfaces with React',
            'skills': ['HTML', 'CSS', 'JavaScript', 'React', 'Tailwind CSS'],
            'status': 'Open'
        },
        {
            'title': 'Database Administrator',
            'company': 'Data Corp',
            'location': 'Hyderabad, India',
            'job_type': 'Full-time',
            'experience': 4,
            'salary': '10-15 LPA',
            'description': 'Manage and optimize database systems',
            'skills': ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Performance Tuning'],
            'status': 'Open'
        },
        {
            'title': 'Python Web Developer',
            'company': 'Web Innovators',
            'location': 'Bangalore, India',
            'job_type': 'Full-time',
            'experience': 2,
            'salary': '7-12 LPA',
            'description': 'Build web applications using Python frameworks',
            'skills': ['Python', 'Flask', 'Django', 'PostgreSQL', 'REST API'],
            'status': 'Open'
        },
        {
            'title': 'Java Full Stack Developer',
            'company': 'Tech Innovators',
            'location': 'Pune, India',
            'job_type': 'Full-time',
            'experience': 3,
            'salary': '10-16 LPA',
            'description': 'Develop full stack applications with Java backend and React frontend',
            'skills': ['Java', 'Spring Boot', 'React', 'JavaScript', 'MySQL'],
            'status': 'Open'
        },
        {
            'title': 'Python Data Engineer',
            'company': 'Big Data Co',
            'location': 'Mumbai, India',
            'job_type': 'Full-time',
            'experience': 3,
            'salary': '12-18 LPA',
            'description': 'Build data pipelines and ETL processes',
            'skills': ['Python', 'Pandas', 'SQL', 'Apache Spark', 'ETL'],
            'status': 'Open'
        },
        {
            'title': 'JavaScript Developer',
            'company': 'Frontend Masters',
            'location': 'Hyderabad, India',
            'job_type': 'Full-time',
            'experience': 2,
            'salary': '7-11 LPA',
            'description': 'Build interactive web applications',
            'skills': ['JavaScript', 'Node.js', 'React', 'HTML', 'CSS'],
            'status': 'Open'
        },
        {
            'title': 'Django Backend Developer',
            'company': 'Backend Pros',
            'location': 'Bangalore, India',
            'job_type': 'Full-time',
            'experience': 3,
            'salary': '10-15 LPA',
            'description': 'Develop robust backend systems with Django',
            'skills': ['Python', 'Django', 'REST API', 'PostgreSQL', 'Redis'],
            'status': 'Open'
        },
        {
            'title': 'Software Engineer - Python/Java',
            'company': 'Multi Tech Corp',
            'location': 'Chennai, India',
            'job_type': 'Full-time',
            'experience': 2,
            'salary': '8-13 LPA',
            'description': 'Work with both Python and Java technologies',
            'skills': ['Python', 'Java', 'Django', 'Spring Boot', 'MySQL'],
            'status': 'Open'
        }
    ]
    
    created_count = 0
    
    for job_data in sample_jobs:
        # Check if job already exists
        existing = Job.objects.filter(
            title=job_data['title'],
            company=job_data['company']
        ).first()
        
        if not existing:
            Job.objects.create(
                posted_by=recruiter,
                **job_data
            )
            created_count += 1
            print(f"✅ Created: {job_data['title']} at {job_data['company']}")
        else:
            print(f"⏭️  Skipped (exists): {job_data['title']}")
    
    print()
    print(f"✅ Created {created_count} new jobs")
    print(f"📊 Total jobs in database: {Job.objects.count()}")


if __name__ == '__main__':
    create_sample_jobs()
