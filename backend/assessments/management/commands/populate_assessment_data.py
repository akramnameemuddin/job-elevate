"""
Management command to populate default skills and sample questions
"""
from django.core.management.base import BaseCommand
from assessments.models import Skill, SkillCategory, QuestionBank


class Command(BaseCommand):
    help = 'Populates default skills and sample assessment questions'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating skills and questions...')
        
        # Create categories and skills with questions
        skills_data = {
            'Programming Languages': {
                'icon': 'bx-code-alt',
                'skills': {
                    'Python': self.get_python_questions(),
                    'JavaScript': self.get_javascript_questions(),
                    'Java': self.get_java_questions(),
                    'C++': self.get_cpp_questions(),
                }
            },
            'Web Development': {
                'icon': 'bx-world',
                'skills': {
                    'HTML/CSS': self.get_html_css_questions(),
                    'React': self.get_react_questions(),
                    'Node.js': self.get_nodejs_questions(),
                    'Django': self.get_django_questions(),
                }
            },
            'Cloud & DevOps': {
                'icon': 'bx-cloud',
                'skills': {
                    'AWS': self.get_aws_questions(),
                    'Docker': self.get_docker_questions(),
                    'Kubernetes': self.get_kubernetes_questions(),
                    'CI/CD': self.get_cicd_questions(),
                }
            },
            'Databases': {
                'icon': 'bx-data',
                'skills': {
                    'SQL': self.get_sql_questions(),
                    'MongoDB': self.get_mongodb_questions(),
                    'PostgreSQL': self.get_postgresql_questions(),
                }
            },
            'Data Science': {
                'icon': 'bx-bar-chart',
                'skills': {
                    'Machine Learning': self.get_ml_questions(),
                    'Data Analysis': self.get_data_analysis_questions(),
                    'TensorFlow': self.get_tensorflow_questions(),
                }
            }
        }
        
        for category_name, category_data in skills_data.items():
            category, _ = SkillCategory.objects.get_or_create(
                name=category_name,
                defaults={'icon': category_data['icon']}
            )
            
            for skill_name, questions in category_data['skills'].items():
                skill, created = Skill.objects.get_or_create(
                    name=skill_name,
                    category=category,
                    defaults={
                        'description': f'Professional {skill_name} development skills',
                        'is_active': True
                    }
                )
                
                if created or not QuestionBank.objects.filter(skill=skill).exists():
                    self.stdout.write(f'  Creating questions for {skill_name}...')
                    for q_data in questions:
                        QuestionBank.objects.get_or_create(
                            skill=skill,
                            question_text=q_data['question'],
                            defaults={
                                'options': q_data['options'],
                                'correct_answer': q_data['correct'],
                                'difficulty': q_data['difficulty'],
                                'points': q_data['points'],
                                'explanation': q_data.get('explanation', ''),
                                'created_by_ai': False,
                            }
                        )
        
        total_skills = Skill.objects.count()
        total_questions = QuestionBank.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'✓ Successfully populated {total_skills} skills with {total_questions} questions'
        ))

    def get_python_questions(self):
        return [
            {
                'question': 'What is the output of: print(type([]) is list)?',
                'options': ['True', 'False', 'None', 'TypeError'],
                'correct': 'True',
                'difficulty': 'easy',
                'points': 5,
            },
            {
                'question': 'Which Python data structure is immutable?',
                'options': ['List', 'Dictionary', 'Tuple', 'Set'],
                'correct': 'Tuple',
                'difficulty': 'easy',
                'points': 5,
            },
            {
                'question': 'What does the "with" statement in Python do?',
                'options': [
                    'Creates a context manager',
                    'Defines a function',
                    'Imports a module',
                    'Handles exceptions'
                ],
                'correct': 'Creates a context manager',
                'difficulty': 'medium',
                'points': 10,
            },
            {
                'question': 'What is a decorator in Python?',
                'options': [
                    'A function that modifies another function',
                    'A class method',
                    'A data type',
                    'A module import'
                ],
                'correct': 'A function that modifies another function',
                'difficulty': 'medium',
                'points': 10,
            },
            {
                'question': 'How do you create a generator in Python?',
                'options': [
                    'Using yield keyword',
                    'Using return keyword',
                    'Using generate() function',
                    'Using lambda'
                ],
                'correct': 'Using yield keyword',
                'difficulty': 'hard',
                'points': 15,
            },
        ]

    def get_javascript_questions(self):
        return [
            {
                'question': 'What is the result of: typeof null?',
                'options': ['"null"', '"object"', '"undefined"', '"number"'],
                'correct': '"object"',
                'difficulty': 'easy',
                'points': 5,
            },
            {
                'question': 'What does "=== " check in JavaScript?',
                'options': [
                    'Value and type equality',
                    'Only value equality',
                    'Only type equality',
                    'Reference equality'
                ],
                'correct': 'Value and type equality',
                'difficulty': 'easy',
                'points': 5,
            },
            {
                'question': 'What is a closure in JavaScript?',
                'options': [
                    'A function with access to parent scope',
                    'A closed loop',
                    'A data structure',
                    'An event handler'
                ],
                'correct': 'A function with access to parent scope',
                'difficulty': 'medium',
                'points': 10,
            },
            {
                'question': 'What is the purpose of async/await?',
                'options': [
                    'Handle asynchronous operations',
                    'Define classes',
                    'Create loops',
                    'Import modules'
                ],
                'correct': 'Handle asynchronous operations',
                'difficulty': 'medium',
                'points': 10,
            },
            {
                'question': 'What is the event loop in JavaScript?',
                'options': [
                    'Mechanism for handling async operations',
                    'A for loop',
                    'An array method',
                    'A variable scope'
                ],
                'correct': 'Mechanism for handling async operations',
                'difficulty': 'hard',
                'points': 15,
            },
        ]

    def get_aws_questions(self):
        return [
            {
                'question': 'What is Amazon S3 used for?',
                'options': ['Object storage', 'Computing', 'Networking', 'Database'],
                'correct': 'Object storage',
                'difficulty': 'easy',
                'points': 5,
            },
            {
                'question': 'What does EC2 stand for?',
                'options': [
                    'Elastic Compute Cloud',
                    'Enhanced Cloud Computing',
                    'Elastic Container Cloud',
                    'Extended Computing Capacity'
                ],
                'correct': 'Elastic Compute Cloud',
                'difficulty': 'easy',
                'points': 5,
            },
            {
                'question': 'Which AWS service is used for DNS management?',
                'options': ['Route 53', 'CloudFront', 'VPC', 'Lambda'],
                'correct': 'Route 53',
                'difficulty': 'medium',
                'points': 10,
            },
        ]

    def get_docker_questions(self):
        return [
            {
                'question': 'What is a Docker container?',
                'options': [
                    'Lightweight isolated environment',
                    'Virtual machine',
                    'Cloud server',
                    'Storage volume'
                ],
                'correct': 'Lightweight isolated environment',
                'difficulty': 'easy',
                'points': 5,
            },
            {
                'question': 'What is the difference between Docker image and container?',
                'options': [
                    'Image is template, container is running instance',
                    'They are the same',
                    'Image is bigger than container',
                    'Container is template'
                ],
                'correct': 'Image is template, container is running instance',
                'difficulty': 'medium',
                'points': 10,
            },
        ]

    def get_kubernetes_questions(self):
        return [
            {
                'question': 'What is a Kubernetes Pod?',
                'options': [
                    'Smallest deployable unit',
                    'A container',
                    'A cluster',
                    'A service'
                ],
                'correct': 'Smallest deployable unit',
                'difficulty': 'medium',
                'points': 10,
            },
        ]

    def get_sql_questions(self):
        return [
            {
                'question': 'What does SQL stand for?',
                'options': [
                    'Structured Query Language',
                    'Simple Query Language',
                    'Standard Query Language',
                    'System Query Language'
                ],
                'correct': 'Structured Query Language',
                'difficulty': 'easy',
                'points': 5,
            },
            {
                'question': 'Which SQL command is used to retrieve data?',
                'options': ['SELECT', 'GET', 'FETCH', 'RETRIEVE'],
                'correct': 'SELECT',
                'difficulty': 'easy',
                'points': 5,
            },
        ]

    def get_ml_questions(self):
        return [
            {
                'question': 'What is supervised learning?',
                'options': [
                    'Learning from labeled data',
                    'Learning without data',
                    'Learning from unlabeled data',
                    'Learning with supervision'
                ],
                'correct': 'Learning from labeled data',
                'difficulty': 'medium',
                'points': 10,
            },
        ]

    # Stub methods for other skills
    def get_java_questions(self):
        return [{
            'question': 'What is JVM?',
            'options': ['Java Virtual Machine', 'Java Version Manager', 'Java Visual Method', 'Java Variable Memory'],
            'correct': 'Java Virtual Machine',
            'difficulty': 'easy',
            'points': 5,
        }]

    def get_cpp_questions(self):
        return [{
            'question': 'What is a pointer in C++?',
            'options': ['Variable storing memory address', 'Data type', 'Function', 'Class'],
            'correct': 'Variable storing memory address',
            'difficulty': 'medium',
            'points': 10,
        }]

    def get_html_css_questions(self):
        return [{
            'question': 'What does CSS stand for?',
            'options': ['Cascading Style Sheets', 'Computer Style Sheets', 'Creative Style Sheets', 'Colorful Style Sheets'],
            'correct': 'Cascading Style Sheets',
            'difficulty': 'easy',
            'points': 5,
        }]

    def get_react_questions(self):
        return [{
            'question': 'What is JSX?',
            'options': ['JavaScript XML', 'Java Syntax Extension', 'JSON XML', 'JavaScript Extension'],
            'correct': 'JavaScript XML',
            'difficulty': 'easy',
            'points': 5,
        }]

    def get_nodejs_questions(self):
        return [{
            'question': 'What is Node.js?',
            'options': ['JavaScript runtime', 'Framework', 'Library', 'Database'],
            'correct': 'JavaScript runtime',
            'difficulty': 'easy',
            'points': 5,
        }]

    def get_django_questions(self):
        return [{
            'question': 'What is Django ORM?',
            'options': ['Object-Relational Mapping', 'Object Resource Manager', 'Online Resource Management', 'Object Routing Module'],
            'correct': 'Object-Relational Mapping',
            'difficulty': 'medium',
            'points': 10,
        }]

    def get_cicd_questions(self):
        return [{
            'question': 'What does CI/CD stand for?',
            'options': ['Continuous Integration/Continuous Deployment', 'Code Integration/Code Deployment', 'Computer Integration/Cloud Deployment', 'Continuous Inspection/Continuous Development'],
            'correct': 'Continuous Integration/Continuous Deployment',
            'difficulty': 'easy',
            'points': 5,
        }]

    def get_mongodb_questions(self):
        return [{
            'question': 'What type of database is MongoDB?',
            'options': ['NoSQL document database', 'SQL database', 'Graph database', 'Key-value store'],
            'correct': 'NoSQL document database',
            'difficulty': 'easy',
            'points': 5,
        }]

    def get_postgresql_questions(self):
        return [{
            'question': 'What is PostgreSQL?',
            'options': ['Open-source relational database', 'NoSQL database', 'Cache store', 'Message queue'],
            'correct': 'Open-source relational database',
            'difficulty': 'easy',
            'points': 5,
        }]

    def get_data_analysis_questions(self):
        return [{
            'question': 'What is data cleaning?',
            'options': ['Preparing data for analysis', 'Deleting data', 'Backing up data', 'Encrypting data'],
            'correct': 'Preparing data for analysis',
            'difficulty': 'easy',
            'points': 5,
        }]

    def get_tensorflow_questions(self):
        return [{
            'question': 'What is TensorFlow?',
            'options': ['Machine learning framework', 'Database', 'Web server', 'Programming language'],
            'correct': 'Machine learning framework',
            'difficulty': 'medium',
            'points': 10,
        }]
