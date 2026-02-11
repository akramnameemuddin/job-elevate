"""
Seed realistic demo data for ML model training and project demonstration.

Usage
-----
    python manage.py seed_demo_data
    python manage.py seed_demo_data --clear   # reset demo data first
"""

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

# ══════════════════════════════════════════════════════════════════
#  Demo Users (10 realistic Indian college profiles)
# ══════════════════════════════════════════════════════════════════
DEMO_USERS = [
    {
        'username': 'rahul_iit', 'full_name': 'Rahul Sharma',
        'email': 'rahul@demo.com', 'user_type': 'student',
        'technical_skills': 'Python, Django, SQL, React, JavaScript, HTML, CSS',
        'soft_skills': 'Team Leadership, Communication',
        'experience': 0, 'degree': 'B.Tech CSE', 'university': 'IIT Hyderabad',
        'graduation_year': 2026, 'cgpa': 8.7,
        'objective': 'Aspiring full-stack developer with strong Python and React skills',
        'projects': '[{"title":"E-Commerce API","description":"REST API with Django and DRF"},{"title":"Chat App","description":"Real-time chat using WebSockets"}]',
        'certifications': '[{"name":"AWS Cloud Practitioner","description":"Amazon Web Services"}]',
    },
    {
        'username': 'priya_nit', 'full_name': 'Priya Reddy',
        'email': 'priya@demo.com', 'user_type': 'student',
        'technical_skills': 'Python, Machine Learning, NumPy, Pandas, TensorFlow, SQL',
        'soft_skills': 'Problem Solving, Research',
        'experience': 1, 'degree': 'B.Tech AI/ML', 'university': 'NIT Warangal',
        'graduation_year': 2025, 'cgpa': 9.1,
        'objective': 'ML engineer with hands-on experience in deep learning and NLP projects',
        'projects': '[{"title":"Sentiment Analyzer","description":"LSTM-based tweet sentiment analysis"},{"title":"Object Detection","description":"YOLOv5 based real-time detector"}]',
        'certifications': '[{"name":"Deep Learning Specialization","description":"Coursera - Andrew Ng"}]',
    },
    {
        'username': 'vikram_bits', 'full_name': 'Vikram Patel',
        'email': 'vikram@demo.com', 'user_type': 'professional',
        'technical_skills': 'Java, Spring Boot, Microservices, Docker, Kubernetes, AWS',
        'soft_skills': 'Architecture Design, Mentoring',
        'experience': 3, 'degree': 'M.Tech SE', 'university': 'BITS Pilani',
        'graduation_year': 2023, 'cgpa': 8.3,
        'objective': 'Backend developer with 3 years of enterprise Java and cloud deployment experience',
        'work_experience': '[{"title":"SDE-1","company":"Infosys","duration":"2 years"},{"title":"SDE-2","company":"Flipkart","duration":"1 year"}]',
        'certifications': '[{"name":"AWS Solutions Architect","description":"Associate level"}]',
    },
    {
        'username': 'sneha_vit', 'full_name': 'Sneha Kumar',
        'email': 'sneha@demo.com', 'user_type': 'student',
        'technical_skills': 'HTML, CSS, JavaScript, Figma, Photoshop',
        'soft_skills': 'Creativity, UX Research',
        'experience': 0, 'degree': 'B.Des', 'university': 'VIT Vellore',
        'graduation_year': 2026, 'cgpa': 8.0,
        'objective': 'UI/UX designer transitioning to frontend development',
        'projects': '[{"title":"Portfolio Website","description":"Personal responsive portfolio with animations"}]',
    },
    {
        'username': 'arjun_iiit', 'full_name': 'Arjun Nair',
        'email': 'arjun@demo.com', 'user_type': 'student',
        'technical_skills': 'Python, PySpark, SQL, Hadoop, Data Modelling, Power BI, Excel',
        'soft_skills': 'Analytical Thinking, Presentation',
        'experience': 0, 'degree': 'B.Tech Data Science', 'university': 'IIIT Bangalore',
        'graduation_year': 2026, 'cgpa': 8.5,
        'objective': 'Data analyst with strong SQL and visualization skills seeking analytics roles',
        'projects': '[{"title":"Sales Dashboard","description":"Power BI dashboard for retail analytics"},{"title":"ETL Pipeline","description":"PySpark pipeline for data warehouse"}]',
    },
    {
        'username': 'meera_srm', 'full_name': 'Meera Iyer',
        'email': 'meera@demo.com', 'user_type': 'professional',
        'technical_skills': 'Python, Django, Flask, PostgreSQL, Redis, Celery, Docker',
        'soft_skills': 'Code Review, Technical Writing',
        'experience': 2, 'degree': 'M.Tech CSE', 'university': 'SRM University',
        'graduation_year': 2024, 'cgpa': 8.8,
        'objective': 'Python backend developer with production experience in Django and Flask',
        'work_experience': '[{"title":"Python Developer","company":"Zoho","duration":"2 years"}]',
        'certifications': '[{"name":"Django Certified Developer","description":"Django Software Foundation"}]',
    },
    {
        'username': 'karthik_amrita', 'full_name': 'Karthik Menon',
        'email': 'karthik@demo.com', 'user_type': 'student',
        'technical_skills': 'C++, Python, Data Structures, Algorithms',
        'soft_skills': 'Logical Thinking, Competitive Spirit',
        'experience': 0, 'degree': 'B.Tech CSE', 'university': 'Amrita University',
        'graduation_year': 2026, 'cgpa': 7.6,
        'objective': 'Competitive programmer aiming for SDE roles at product companies',
        'projects': '[{"title":"Custom STL Library","description":"Implemented red-black trees and hash maps in C++"}]',
    },
    {
        'username': 'ananya_manipal', 'full_name': 'Ananya Gupta',
        'email': 'ananya@demo.com', 'user_type': 'student',
        'technical_skills': 'Python, React, Node.js, MongoDB, Express, Git',
        'soft_skills': 'Collaboration, Agile',
        'experience': 0, 'degree': 'B.Tech IT', 'university': 'Manipal University',
        'graduation_year': 2026, 'cgpa': 8.2,
        'objective': 'MERN stack developer interested in building scalable web applications',
        'projects': '[{"title":"Task Manager","description":"Full-stack MERN app with JWT auth"},{"title":"Blog Platform","description":"Next.js blog with MDX support"}]',
    },
    {
        'username': 'deepak_vvit', 'full_name': 'Deepak Rao',
        'email': 'deepak@demo.com', 'user_type': 'professional',
        'technical_skills': 'DevOps, AWS, Terraform, Jenkins, Docker, Kubernetes, Linux, Bash',
        'soft_skills': 'Incident Management, Documentation',
        'experience': 4, 'degree': 'B.Tech CSE', 'university': 'VVIT',
        'graduation_year': 2022, 'cgpa': 7.9,
        'objective': 'DevOps engineer with 4 years managing cloud infrastructure at scale',
        'work_experience': '[{"title":"DevOps Engineer","company":"TCS","duration":"2 years"},{"title":"Sr DevOps","company":"Razorpay","duration":"2 years"}]',
        'certifications': '[{"name":"AWS DevOps Professional","description":"Amazon"},{"name":"CKA","description":"Certified Kubernetes Admin"}]',
    },
    {
        'username': 'fatima_jntu', 'full_name': 'Fatima Sheikh',
        'email': 'fatima@demo.com', 'user_type': 'student',
        'technical_skills': 'Python, R, Statistics, Machine Learning, Tableau, SQL',
        'soft_skills': 'Data Storytelling, Attention to Detail',
        'experience': 0, 'degree': 'M.Sc Statistics', 'university': 'JNTU Hyderabad',
        'graduation_year': 2026, 'cgpa': 9.0,
        'objective': 'Statistics graduate transitioning into data science and analytics roles',
        'projects': '[{"title":"Customer Churn Model","description":"Random Forest model predicting churn with 85% accuracy"},{"title":"AB Testing Framework","description":"Statistical testing tool for marketing experiments"}]',
    },
]

# ══════════════════════════════════════════════════════════════════
#  Demo Recruiters (1 per company — 4 companies, 2 jobs each)
# ══════════════════════════════════════════════════════════════════
DEMO_RECRUITERS = [
    {
        'username': 'rec_techmahindra', 'full_name': 'Anil Kapoor',
        'email': 'anil.rec@demo.com', 'company_name': 'TechMahindra',
    },
    {
        'username': 'rec_zoho', 'full_name': 'Lakshmi Venkatesh',
        'email': 'lakshmi.rec@demo.com', 'company_name': 'Zoho Corporation',
    },
    {
        'username': 'rec_fractal', 'full_name': 'Sanjay Mishra',
        'email': 'sanjay.rec@demo.com', 'company_name': 'Fractal Analytics',
    },
    {
        'username': 'rec_amazon', 'full_name': 'Divya Krishnan',
        'email': 'divya.rec@demo.com', 'company_name': 'Amazon',
    },
]

# Maps each DEMO_JOBS index → DEMO_RECRUITERS index (1 recruiter per company)
JOB_RECRUITER_MAP = [0, 2, 1, 3, 2, 1, 0, 3]

# ══════════════════════════════════════════════════════════════════
#  Demo Jobs (8 real-looking Indian tech roles)
# ══════════════════════════════════════════════════════════════════
DEMO_JOBS = [
    {
        'title': 'Python Backend Developer', 'company': 'TechMahindra',
        'location': 'Hyderabad', 'job_type': 'Full-time',
        'skills': ['Python', 'Django', 'SQL', 'REST API', 'Docker'],
        'experience': 1, 'salary': '6,00,000 - 9,00,000',
        'description': 'Build and maintain scalable REST APIs using Django and PostgreSQL for enterprise clients.',
        'requirements': 'Strong Python, ORM, database design. Experience with Docker preferred.',
    },
    {
        'title': 'ML Engineer Intern', 'company': 'Fractal Analytics',
        'location': 'Bengaluru', 'job_type': 'Internship',
        'skills': ['Python', 'Machine Learning', 'TensorFlow', 'NumPy', 'Pandas'],
        'experience': 0, 'salary': '25,000 - 40,000 /month',
        'description': 'Work on production ML pipelines for NLP and computer vision tasks.',
        'requirements': 'Strong fundamentals in ML, linear algebra, probability.',
    },
    {
        'title': 'Frontend Developer', 'company': 'Zoho Corporation',
        'location': 'Chennai', 'job_type': 'Full-time',
        'skills': ['JavaScript', 'React', 'HTML', 'CSS', 'Git'],
        'experience': 0, 'salary': '5,00,000 - 8,00,000',
        'description': 'Build responsive UI components for Zoho suite of products.',
        'requirements': 'HTML/CSS mastery, JavaScript ES6+, React or Vue.',
    },
    {
        'title': 'DevOps Engineer', 'company': 'Amazon',
        'location': 'Pune', 'job_type': 'Full-time',
        'skills': ['Docker', 'Kubernetes', 'AWS', 'Jenkins', 'Terraform'],
        'experience': 2, 'salary': '8,00,000 - 12,00,000',
        'description': 'Manage CI/CD pipelines and cloud infrastructure on AWS.',
        'requirements': '2+ years in DevOps, strong Linux and scripting skills.',
    },
    {
        'title': 'Data Analyst', 'company': 'Fractal Analytics',
        'location': 'Hyderabad', 'job_type': 'Full-time',
        'skills': ['SQL', 'Python', 'Power BI', 'Excel', 'Data Modelling'],
        'experience': 0, 'salary': '4,00,000 - 7,00,000',
        'description': 'Analyze business data and create dashboards for stakeholder reporting.',
        'requirements': 'Strong SQL, advanced Excel, any BI tool.',
    },
    {
        'title': 'MERN Stack Developer', 'company': 'Zoho Corporation',
        'location': 'Bengaluru', 'job_type': 'Full-time',
        'skills': ['React', 'Node.js', 'MongoDB', 'Express', 'JavaScript'],
        'experience': 1, 'salary': '7,00,000 - 11,00,000',
        'description': 'Full-stack development for enterprise product suite.',
        'requirements': 'Proficiency in React, Node.js, MongoDB, REST APIs.',
    },
    {
        'title': 'Java Backend Developer', 'company': 'TechMahindra',
        'location': 'Bengaluru', 'job_type': 'Full-time',
        'skills': ['Java', 'Spring Boot', 'Microservices', 'SQL', 'Docker'],
        'experience': 2, 'salary': '7,00,000 - 10,00,000',
        'description': 'Build microservices for enterprise banking platform.',
        'requirements': 'Java 11+, Spring ecosystem, SQL databases.',
    },
    {
        'title': 'Cloud Engineer Intern', 'company': 'Amazon',
        'location': 'Hyderabad', 'job_type': 'Internship',
        'skills': ['AWS', 'Linux', 'Docker', 'Python', 'Bash'],
        'experience': 0, 'salary': '40,000 - 60,000 /month',
        'description': 'Support cloud infra team writing automation scripts and IaC.',
        'requirements': 'Linux basics, any programming language, AWS familiarity.',
    },
]

# ══════════════════════════════════════════════════════════════════
#  Application outcomes — realistic hiring patterns
#  (user_index, job_index, status)
# ══════════════════════════════════════════════════════════════════
DEMO_APPLICATIONS = [
    # ── Positive outcomes (skills match well) ─────────────────────
    (0, 0, 'Hired'),       # rahul → Python Backend (has python,django,sql)
    (1, 1, 'Hired'),       # priya → ML Intern (has ml,tensorflow,numpy,pandas)
    (2, 6, 'Hired'),       # vikram → Java Backend (has java,spring,microservices)
    (4, 4, 'Hired'),       # arjun → Data Analyst (has sql,python,power-bi)
    (5, 0, 'Offered'),     # meera → Python Backend (has python,django,docker)
    (8, 3, 'Hired'),       # deepak → DevOps (has docker,k8s,aws,terraform)
    (7, 2, 'Interview'),   # ananya → Frontend (has react,javascript)
    (9, 4, 'Shortlisted'), # fatima → Data Analyst (has python,sql,tableau)
    (3, 2, 'Shortlisted'), # sneha → Frontend (has html,css,javascript)
    (2, 3, 'Shortlisted'), # vikram → DevOps (has docker,k8s,aws)
    (8, 7, 'Offered'),     # deepak → Cloud Intern (overqualified: aws,linux,docker)
    (7, 5, 'Interview'),   # ananya → MERN Stack (has react,node,mongodb,express)

    # ── Negative outcomes (skills don't match) ────────────────────
    (6, 0, 'Rejected'),    # karthik → Python Backend (only c++,python — no django/sql)
    (3, 1, 'Rejected'),    # sneha → ML Intern (no ML skills at all)
    (0, 3, 'Rejected'),    # rahul → DevOps (no docker,k8s,aws)
    (9, 2, 'Rejected'),    # fatima → Frontend (no frontend skills)
    (6, 6, 'Rejected'),    # karthik → Java Backend (no java/spring)
    (5, 5, 'Rejected'),    # meera → MERN Stack (no react/node/mongo)
    (1, 3, 'Rejected'),    # priya → DevOps (no docker/k8s/aws)
    (4, 6, 'Rejected'),    # arjun → Java Backend (no java/spring)

    # ── Pending (no outcome yet) ──────────────────────────────────
    (1, 4, 'Applied'),     # priya → Data Analyst
    (0, 5, 'Applied'),     # rahul → MERN Stack
]

# ── Skill proficiency lookup (base values ± per-user variation) ────
_PROF = {
    'python': 8.2, 'django': 7.5, 'sql': 7.8, 'react': 7.3,
    'javascript': 7.0, 'html': 8.5, 'css': 8.2, 'java': 8.0,
    'spring boot': 7.3, 'microservices': 6.8, 'docker': 7.5,
    'kubernetes': 6.2, 'aws': 7.0, 'machine learning': 7.8,
    'tensorflow': 6.8, 'numpy': 8.3, 'pandas': 8.5,
    'node.js': 6.8, 'mongodb': 6.5, 'express': 6.2,
    'power bi': 7.3, 'excel': 8.0, 'data modelling': 7.0,
    'pyspark': 5.8, 'figma': 7.8, 'c++': 8.3,
    'data structures': 8.8, 'algorithms': 8.3,
    'terraform': 6.8, 'jenkins': 7.2, 'linux': 7.8,
    'bash': 7.2, 'git': 7.8, 'r': 6.3, 'statistics': 7.5,
    'tableau': 6.8, 'flask': 7.3, 'postgresql': 7.5,
    'redis': 6.2, 'celery': 5.8, 'hadoop': 5.3,
    'rest api': 7.3, 'photoshop': 6.8, 'devops': 7.5,
}


class Command(BaseCommand):
    help = 'Seed realistic demo users, jobs, and application outcomes for ML training'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Delete all demo data (@demo.com users) before seeding',
        )

    def handle(self, *args, **options):
        from assessments.models import Skill, SkillCategory, UserSkillScore
        from recruiter.models import Application, Job

        rng = random.Random(42)

        if options['clear']:
            self.stdout.write('Clearing demo data …')
            User.objects.filter(email__endswith='@demo.com').delete()
            Job.objects.filter(title__in=[j['title'] for j in DEMO_JOBS]).delete()

        # ── Recruiter accounts (1 per company) ─────────────────
        recruiters = []
        for r in DEMO_RECRUITERS:
            obj, cr = User.objects.get_or_create(
                username=r['username'],
                defaults={
                    'email': r['email'],
                    'full_name': r['full_name'],
                    'user_type': 'recruiter',
                    'company_name': r['company_name'],
                    'email_verified': True,
                },
            )
            if cr:
                obj.set_password('demo1234')
                obj.save()
                self.stdout.write(f'  + Recruiter: {obj.full_name} ({r["company_name"]})')
            recruiters.append(obj)

        # ── Users ─────────────────────────────────────────────────
        users = []
        for u in DEMO_USERS:
            obj, cr = User.objects.get_or_create(
                username=u['username'],
                defaults={
                    'full_name': u['full_name'],
                    'email': u['email'],
                    'user_type': u['user_type'],
                    'technical_skills': u['technical_skills'],
                    'soft_skills': u.get('soft_skills', ''),
                    'experience': u['experience'],
                    'degree': u['degree'],
                    'university': u['university'],
                    'graduation_year': u.get('graduation_year'),
                    'cgpa': u.get('cgpa', 0),
                    'objective': u.get('objective', ''),
                    'projects': u.get('projects', ''),
                    'certifications': u.get('certifications', ''),
                    'work_experience': u.get('work_experience', ''),
                    'email_verified': True,
                },
            )
            if cr:
                obj.set_password('demo1234')
                obj.save()
                self.stdout.write(f'  + User: {obj.full_name}')
            users.append(obj)

        # ── Skill scores ──────────────────────────────────────────
        cat, _ = SkillCategory.objects.get_or_create(
            name='Technical', defaults={'description': 'Technical skills'},
        )
        for user in users:
            skill_names = [
                s.strip() for s in (user.technical_skills or '').split(',') if s.strip()
            ]
            for sn in skill_names:
                # Find existing skill by name (case-insensitive) before creating
                skill_obj = Skill.objects.filter(name__iexact=sn).first()
                if not skill_obj:
                    skill_obj, _ = Skill.objects.get_or_create(
                        name=sn, category=cat,
                        defaults={'description': f'{sn} skill', 'is_active': True},
                    )
                base = _PROF.get(sn.lower(), 6.0)
                verified = rng.random() < 0.7
                vl = round(max(1.0, min(10.0, base + rng.uniform(-1.5, 1.5))), 1)
                sr = round(max(1.0, min(10.0, vl + rng.uniform(-0.5, 1.5))), 1)

                UserSkillScore.objects.update_or_create(
                    user=user, skill=skill_obj,
                    defaults={
                        'verified_level': vl if verified else 0,
                        'self_rated_level': sr,
                        'status': 'verified' if verified else 'claimed',
                        'total_attempts': rng.randint(1, 3) if verified else 0,
                        'best_score_percentage': round(vl * 10, 1) if verified else 0,
                    },
                )

        # ── Jobs ──────────────────────────────────────────────────
        jobs = []
        for i, j in enumerate(DEMO_JOBS):
            rec = recruiters[JOB_RECRUITER_MAP[i]]
            obj, cr = Job.objects.get_or_create(
                title=j['title'], company=j['company'],
                defaults={
                    'posted_by': rec,
                    'location': j['location'],
                    'job_type': j['job_type'],
                    'skills': j['skills'],
                    'experience': j['experience'],
                    'salary': j['salary'],
                    'description': j['description'],
                    'requirements': j.get('requirements', ''),
                    'status': 'Open',
                },
            )
            if cr:
                self.stdout.write(f'  + Job:  {obj.title} @ {obj.company}')
            jobs.append(obj)

        # ── Applications with outcomes ────────────────────────────
        app_count = 0
        for ui, ji, status in DEMO_APPLICATIONS:
            _, cr = Application.objects.get_or_create(
                applicant=users[ui], job=jobs[ji],
                defaults={'status': status},
            )
            if cr:
                app_count += 1

        # ── Summary ───────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
        self.stdout.write(f'  Users:        {len(users)} (+ {len(recruiters)} recruiters)')
        self.stdout.write(f'  Jobs:         {len(jobs)}')
        self.stdout.write(f'  Applications: {app_count}')
        pos = sum(1 for _, _, s in DEMO_APPLICATIONS if s in ('Hired', 'Offered', 'Interview', 'Shortlisted'))
        neg = sum(1 for _, _, s in DEMO_APPLICATIONS if s == 'Rejected')
        self.stdout.write(f'    Positive outcomes (Hired/Offered/Interview/Shortlisted): {pos}')
        self.stdout.write(f'    Negative outcomes (Rejected): {neg}')
        self.stdout.write(f'    Pending (Applied): {len(DEMO_APPLICATIONS) - pos - neg}')
        self.stdout.write('')
        self.stdout.write('  Next:  python manage.py train_fit_model')
