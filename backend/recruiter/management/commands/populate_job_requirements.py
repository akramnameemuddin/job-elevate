"""
Management command to populate sample job skill requirements
This helps test the skill intelligence engine
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from recruiter.models import Job, JobSkillRequirement
from assessments.models import Skill, SkillCategory


class Command(BaseCommand):
    help = 'Populate sample job skill requirements for testing'

    def handle(self, *args, **options):
        self.stdout.write('Populating job skill requirements...')
        
        with transaction.atomic():
            # Get or create common skills
            programming_cat, _ = SkillCategory.objects.get_or_create(
                name='Programming',
                defaults={'description': 'Programming languages and frameworks'}
            )
            
            data_cat, _ = SkillCategory.objects.get_or_create(
                name='Data Analysis',
                defaults={'description': 'Data analysis and statistics'}
            )
            
            web_cat, _ = SkillCategory.objects.get_or_create(
                name='Web Development',
                defaults={'description': 'Web development technologies'}
            )
            
            # Create skills
            skills_data = [
                # Programming
                (programming_cat, 'Python', 'Python programming language'),
                (programming_cat, 'JavaScript', 'JavaScript programming'),
                (programming_cat, 'Java', 'Java programming language'),
                (programming_cat, 'C++', 'C++ programming'),
                (programming_cat, 'SQL', 'SQL database queries'),
                
                # Data Analysis
                (data_cat, 'Data Analysis', 'Statistical data analysis'),
                (data_cat, 'Machine Learning', 'ML algorithms and models'),
                (data_cat, 'Pandas', 'Python pandas library'),
                (data_cat, 'NumPy', 'Python NumPy library'),
                (data_cat, 'Excel', 'Microsoft Excel'),
                
                # Web Development
                (web_cat, 'React', 'React.js framework'),
                (web_cat, 'Django', 'Django web framework'),
                (web_cat, 'HTML/CSS', 'HTML and CSS'),
                (web_cat, 'REST APIs', 'RESTful API design'),
                (web_cat, 'Git', 'Version control with Git'),
            ]
            
            skills = {}
            for cat, name, desc in skills_data:
                skill, created = Skill.objects.get_or_create(
                    category=cat,
                    name=name,
                    defaults={'description': desc}
                )
                skills[name] = skill
                if created:
                    self.stdout.write(f'  Created skill: {name}')
            
            # Get sample jobs
            jobs = Job.objects.filter(status='Open')[:10]
            
            if not jobs:
                self.stdout.write(self.style.WARNING('No open jobs found. Please create jobs first.'))
                return
            
            # Define requirement templates by job type
            requirement_templates = {
                'data': [
                    ('Python', 7.0, 0.9, True, 2.0),
                    ('SQL', 6.0, 0.8, True, 1.5),
                    ('Data Analysis', 7.5, 1.0, True, 2.5),
                    ('Machine Learning', 6.0, 0.7, False, 1.5),
                    ('Pandas', 6.5, 0.7, False, 1.0),
                    ('NumPy', 5.0, 0.5, False, 1.0),
                    ('Excel', 5.0, 0.4, False, 0.8),
                ],
                'web': [
                    ('JavaScript', 7.0, 0.9, True, 2.0),
                    ('React', 6.5, 0.8, True, 1.8),
                    ('HTML/CSS', 7.0, 0.8, True, 1.5),
                    ('REST APIs', 6.0, 0.7, False, 1.2),
                    ('Git', 5.0, 0.6, False, 1.0),
                    ('Django', 5.0, 0.5, False, 1.0),
                ],
                'fullstack': [
                    ('Python', 7.0, 0.8, True, 1.5),
                    ('JavaScript', 7.0, 0.8, True, 1.5),
                    ('React', 6.0, 0.7, False, 1.2),
                    ('Django', 6.5, 0.7, True, 1.5),
                    ('SQL', 6.0, 0.7, False, 1.2),
                    ('REST APIs', 7.0, 0.8, True, 1.5),
                    ('Git', 5.0, 0.6, False, 1.0),
                ],
                'software': [
                    ('Python', 6.0, 0.7, False, 1.2),
                    ('Java', 7.0, 0.8, True, 1.8),
                    ('SQL', 5.0, 0.6, False, 1.0),
                    ('Git', 6.0, 0.7, True, 1.2),
                    ('REST APIs', 6.0, 0.6, False, 1.0),
                ],
            }
            
            # Apply requirements to jobs
            for job in jobs:
                # Determine job type from title
                title_lower = job.title.lower()
                
                if 'data' in title_lower or 'analyst' in title_lower or 'scientist' in title_lower:
                    template = requirement_templates['data']
                elif 'web' in title_lower or 'frontend' in title_lower or 'react' in title_lower:
                    template = requirement_templates['web']
                elif 'fullstack' in title_lower or 'full stack' in title_lower:
                    template = requirement_templates['fullstack']
                else:
                    template = requirement_templates['software']
                
                # Create requirements
                for skill_name, proficiency, criticality, is_mandatory, weight in template:
                    if skill_name in skills:
                        req, created = JobSkillRequirement.objects.get_or_create(
                            job=job,
                            skill=skills[skill_name],
                            defaults={
                                'required_proficiency': proficiency,
                                'criticality': criticality,
                                'is_mandatory': is_mandatory,
                                'weight': weight,
                                'years_required': max(0, int((proficiency - 4) / 2))
                            }
                        )
                        
                        if created:
                            self.stdout.write(
                                f'  Added {skill_name} requirement to {job.title} '
                                f'(proficiency: {proficiency}, criticality: {criticality})'
                            )
            
            self.stdout.write(self.style.SUCCESS('✅ Successfully populated job skill requirements!'))
