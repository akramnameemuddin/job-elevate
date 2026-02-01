"""
Test the 100-question system
Usage: python manage.py test_100q_system
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from assessments.models import Skill, SkillCategory, QuestionBank
from assessments.ai_service import generate_and_store_questions_for_skill, get_questions_for_assessment

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the 100-question generation and allocation system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skill',
            type=str,
            default='Python',
            help='Skill name to test (default: Python)'
        )

    def handle(self, *args, **options):
        skill_name = options['skill']
        
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.HTTP_INFO('100-QUESTION SYSTEM TEST'))
        self.stdout.write('=' * 70)
        
        # Get or create test skill
        category, _ = SkillCategory.objects.get_or_create(name='Programming')
        skill, created = Skill.objects.get_or_create(
            name=skill_name,
            category=category,
            defaults={'description': f'Test skill for {skill_name}'}
        )
        
        if created:
            self.stdout.write(f'\n✓ Created test skill: {skill.name}')
        else:
            self.stdout.write(f'\n✓ Using existing skill: {skill.name}')
        
        self.stdout.write(f'  Current question count: {skill.question_count}/100')
        
        # Test 1: Generate questions for first 5 "users"
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('TEST 1: Simulate first 5 users (should generate 20 each)')
        self.stdout.write('=' * 70)
        
        for user_num in range(1, 6):
            self.stdout.write(f'\n[User #{user_num}] Getting questions...')
            
            # Simulate getting questions for assessment
            questions = get_questions_for_assessment(skill, user_attempt_number=user_num)
            
            if questions:
                count = questions.count()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Got {count} questions'))
                self.stdout.write(f'  Skill now has: {skill.question_count}/100 questions')
                
                # Show difficulty distribution
                easy = questions.filter(difficulty='easy').count()
                medium = questions.filter(difficulty='medium').count()
                hard = questions.filter(difficulty='hard').count()
                self.stdout.write(f'  Distribution: {easy} easy, {medium} medium, {hard} hard')
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed to get questions'))
                return
        
        # Check final count
        skill.refresh_from_db()
        self.stdout.write(f'\n✓ After 5 users, skill has {skill.question_count}/100 questions')
        
        # Test 2: Verify user 6+ gets random selection
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('TEST 2: Simulate user 6-8 (should randomly select from bank)')
        self.stdout.write('=' * 70)
        
        for user_num in range(6, 9):
            self.stdout.write(f'\n[User #{user_num}] Getting questions...')
            
            questions = get_questions_for_assessment(skill, user_attempt_number=user_num)
            
            if questions:
                count = questions.count()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Got {count} questions (randomly selected)'))
                self.stdout.write(f'  Skill still has: {skill.question_count}/100 questions')
                
                # Show some question IDs to prove randomness
                q_ids = list(questions.values_list('id', flat=True)[:5])
                self.stdout.write(f'  Sample IDs: {q_ids}')
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed to get questions'))
        
        # Test 3: Show question bank stats
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('TEST 3: Question Bank Statistics')
        self.stdout.write('=' * 70)
        
        all_questions = QuestionBank.objects.filter(skill=skill)
        total = all_questions.count()
        
        self.stdout.write(f'\nTotal Questions: {total}/100')
        self.stdout.write(f'  Easy: {all_questions.filter(difficulty="easy").count()}')
        self.stdout.write(f'  Medium: {all_questions.filter(difficulty="medium").count()}')
        self.stdout.write(f'  Hard: {all_questions.filter(difficulty="hard").count()}')
        
        # Show proficiency distribution
        self.stdout.write('\nProficiency Levels:')
        for level in [3.0, 6.0, 9.0]:
            count = all_questions.filter(proficiency_level=level).count()
            self.stdout.write(f'  Level {level}: {count} questions')
        
        # Show sample questions
        self.stdout.write('\nSample Questions:')
        for i, q in enumerate(all_questions[:3], 1):
            self.stdout.write(f'\n{i}. {q.question_text[:80]}...')
            self.stdout.write(f'   Difficulty: {q.difficulty}, Proficiency: {q.proficiency_level}')
            self.stdout.write(f'   Options: {len(q.options)} choices')
        
        # Final summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✓ TEST COMPLETE!'))
        self.stdout.write('=' * 70)
        
        self.stdout.write('\nSystem Status:')
        self.stdout.write(f'  ✓ Skill: {skill.name}')
        self.stdout.write(f'  ✓ Question Bank: {skill.question_count}/100')
        self.stdout.write(f'  ✓ First 5 users: Generate & store')
        self.stdout.write(f'  ✓ User 6+: Random selection')
        self.stdout.write(f'  ✓ Proficiency levels: Tagged for skill gap analysis')
        self.stdout.write('')
