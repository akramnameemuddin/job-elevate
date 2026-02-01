"""
Management command to clean up assessment data for 100-question system
Usage: python manage.py cleanup_assessment_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from assessments.models import (
    QuestionBank, AssessmentAttempt, UserAnswer, 
    UserSkillScore, Skill, Assessment, Question
)


class Command(BaseCommand):
    help = 'Clean up all assessment data to prepare for 100-question system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion (required to actually delete data)',
        )
        parser.add_argument(
            '--keep-skills',
            action='store_true',
            help='Keep Skill definitions, only delete questions and attempts',
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        keep_skills = options['keep_skills']
        
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.HTTP_INFO('ASSESSMENT DATA CLEANUP'))
        self.stdout.write('=' * 70)
        
        # Count existing data
        question_count = QuestionBank.objects.count()
        attempt_count = AssessmentAttempt.objects.count()
        answer_count = UserAnswer.objects.count()
        score_count = UserSkillScore.objects.count()
        assessment_count = Assessment.objects.count()
        old_question_count = Question.objects.count()
        skill_count = Skill.objects.count()
        
        self.stdout.write('\nCurrent Data:')
        self.stdout.write(f'  • QuestionBank: {question_count} questions')
        self.stdout.write(f'  • AssessmentAttempts: {attempt_count} attempts')
        self.stdout.write(f'  • UserAnswers: {answer_count} answers')
        self.stdout.write(f'  • UserSkillScores: {score_count} scores')
        self.stdout.write(f'  • Assessments (deprecated): {assessment_count}')
        self.stdout.write(f'  • Questions (deprecated): {old_question_count}')
        self.stdout.write(f'  • Skills: {skill_count} skills')
        
        if not confirm:
            self.stdout.write('\n' + self.style.WARNING('⚠ DRY RUN MODE'))
            self.stdout.write('No data will be deleted. Use --confirm to actually delete.')
            self.stdout.write('\nWhat will be deleted:')
            self.stdout.write(f'  ✗ All {question_count} questions in QuestionBank')
            self.stdout.write(f'  ✗ All {attempt_count} assessment attempts')
            self.stdout.write(f'  ✗ All {answer_count} user answers')
            self.stdout.write(f'  ✗ All {score_count} skill scores')
            self.stdout.write(f'  ✗ All {assessment_count} deprecated assessments')
            self.stdout.write(f'  ✗ All {old_question_count} deprecated questions')
            if not keep_skills:
                self.stdout.write(f'  ✗ Reset all {skill_count} skills')
            else:
                self.stdout.write(f'  ✓ Keep {skill_count} skills (--keep-skills flag)')
            
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write('To proceed, run:')
            self.stdout.write(self.style.SUCCESS('  python manage.py cleanup_assessment_data --confirm'))
            if keep_skills:
                self.stdout.write(self.style.SUCCESS('  python manage.py cleanup_assessment_data --confirm --keep-skills'))
            self.stdout.write('=' * 70)
            return
        
        # Confirmed deletion
        self.stdout.write('\n' + self.style.WARNING('⚠ DELETING DATA...'))
        
        try:
            with transaction.atomic():
                from django.db import connection
                cursor = connection.cursor()
                
                # Delete in correct order (foreign key dependencies) using raw SQL
                # to avoid model field mismatches
                
                cursor.execute("DELETE FROM assessments_useranswer")
                deleted_answers = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {deleted_answers} user answers'))
                
                cursor.execute("DELETE FROM assessments_assessmentattempt")
                deleted_attempts = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {deleted_attempts} assessment attempts'))
                
                cursor.execute("DELETE FROM assessments_userskillscore")
                deleted_scores = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {deleted_scores} skill scores'))
                
                cursor.execute("DELETE FROM assessments_questionbank")
                deleted_questions = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {deleted_questions} questions from bank'))
                
                cursor.execute("DELETE FROM assessments_question")
                deleted_old_questions = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {deleted_old_questions} deprecated questions'))
                
                cursor.execute("DELETE FROM assessments_assessment")
                deleted_assessments = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {deleted_assessments} deprecated assessments'))
                
                if not keep_skills:
                    cursor.execute("DELETE FROM assessments_skill")
                    deleted_skills = cursor.rowcount
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {deleted_skills} skills'))
                else:
                    # Reset skill fields using raw SQL (avoid model field issues)
                    cursor.execute("""
                        UPDATE assessments_skill 
                        SET questions_generated = 0,
                            questions_generated_at = NULL
                    """)
                    updated_skills = cursor.rowcount
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Reset {updated_skills} skills'))
                
                self.stdout.write('\n' + '=' * 70)
                self.stdout.write(self.style.SUCCESS('✓ CLEANUP COMPLETE!'))
                self.stdout.write('=' * 70)
                self.stdout.write('Database is now ready for the 100-question system.')
                self.stdout.write('\nNext steps:')
                self.stdout.write('  1. Run migrations: python manage.py migrate')
                self.stdout.write('  2. Start generating questions (will build up to 100 per skill)')
                self.stdout.write('  3. First 5 users per skill get AI-generated questions')
                self.stdout.write('  4. User 6+ get randomly selected from the 100-question bank')
                self.stdout.write('')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ ERROR: {str(e)}'))
            self.stdout.write('Database rolled back. No changes were made.')
            raise
