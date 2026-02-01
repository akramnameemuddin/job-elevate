"""
Test command for on-demand question generation
"""
from django.core.management.base import BaseCommand
from assessments.models import Skill, QuestionBank
from assessments.views import _generate_batch_for_skill


class Command(BaseCommand):
    help = 'Test on-demand question generation for a skill'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skill',
            type=str,
            required=True,
            help='Skill name to test',
        )

    def handle(self, *args, **options):
        skill_name = options['skill']
        
        try:
            skill = Skill.objects.get(name__iexact=skill_name)
        except Skill.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Skill "{skill_name}" not found'))
            return
        
        # Check current count
        current_count = QuestionBank.objects.filter(skill=skill).count()
        self.stdout.write(f'\n{skill.name}: {current_count}/100 questions')
        
        if current_count >= 100:
            self.stdout.write(self.style.SUCCESS('Target reached - no generation needed!'))
            return
        
        # Test generation
        self.stdout.write(f'\nGenerating 20 questions for {skill.name}...')
        self.stdout.write('(This simulates what happens when a user starts an assessment)\n')
        
        success = _generate_batch_for_skill(skill, count=20, required=True)
        
        if success:
            new_count = QuestionBank.objects.filter(skill=skill).count()
            generated = new_count - current_count
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[OK] Generated {generated} questions!'
                )
            )
            self.stdout.write(f'Total: {new_count}/100 questions for {skill.name}')
            
            # Show breakdown
            easy = QuestionBank.objects.filter(skill=skill, difficulty='easy').count()
            medium = QuestionBank.objects.filter(skill=skill, difficulty='medium').count()
            hard = QuestionBank.objects.filter(skill=skill, difficulty='hard').count()
            
            self.stdout.write('\nDifficulty breakdown:')
            self.stdout.write(f'  Easy: {easy}')
            self.stdout.write(f'  Medium: {medium}')
            self.stdout.write(f'  Hard: {hard}')
        else:
            self.stdout.write(self.style.ERROR('\n[ERROR] Generation failed'))
            self.stdout.write('Check logs for details')
