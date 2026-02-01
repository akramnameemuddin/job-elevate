"""
Management command to generate 100 questions for each technical skill.
Uses Google Gemini AI to generate skill-specific, relevant questions.
"""
import json
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from assessments.models import Skill, QuestionBank
from assessments.ai_service import question_generator


class Command(BaseCommand):
    help = 'Generate 100 relevant questions for each technical skill using AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skill',
            type=str,
            help='Generate questions for specific skill name',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing questions',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=20,
            help='Number of questions to generate per batch (default: 20)',
        )

    def handle(self, *args, **options):
        skill_name = options.get('skill')
        overwrite = options.get('overwrite')
        batch_size = options.get('batch_size')

        if skill_name:
            skills = Skill.objects.filter(name__iexact=skill_name, is_active=True)
            if not skills.exists():
                self.stdout.write(self.style.ERROR(f'Skill "{skill_name}" not found'))
                return
        else:
            skills = Skill.objects.filter(is_active=True)

        self.stdout.write(self.style.SUCCESS(f'Generating questions for {skills.count()} skills...'))

        for skill in skills:
            self.generate_questions_for_skill(skill, overwrite, batch_size)

        self.stdout.write(self.style.SUCCESS('[OK] Question generation completed!'))

    def generate_questions_for_skill(self, skill, overwrite, batch_size):
        """Generate 100 questions for a single skill"""
        existing_count = QuestionBank.objects.filter(skill=skill).count()

        if existing_count >= 100 and not overwrite:
            self.stdout.write(
                self.style.WARNING(f'[SKIP] {skill.name}: Already has {existing_count} questions (skipped)')
            )
            return

        if overwrite:
            deleted_count = QuestionBank.objects.filter(skill=skill).delete()[0]
            self.stdout.write(f'  Deleted {deleted_count} existing questions')

        target_count = 100
        current_count = QuestionBank.objects.filter(skill=skill).count()
        needed = target_count - current_count

        if needed <= 0:
            self.stdout.write(self.style.SUCCESS(f'[OK] {skill.name}: Already has {current_count} questions'))
            return

        self.stdout.write(f'> {skill.name}: Generating {needed} questions...')

        # Calculate distribution: 40% easy, 30% medium, 30% hard
        easy_needed = int(needed * 0.4)
        medium_needed = int(needed * 0.3)
        hard_needed = needed - easy_needed - medium_needed

        difficulty_targets = {
            'easy': easy_needed,
            'medium': medium_needed,
            'hard': hard_needed
        }

        total_generated = 0

        for difficulty, count in difficulty_targets.items():
            if count == 0:
                continue

            batches = (count + batch_size - 1) // batch_size  # Ceiling division
            
            for batch_num in range(batches):
                batch_count = min(batch_size, count - (batch_num * batch_size))
                
                # Rate limit: Free tier allows 5 requests per minute
                # Add 15-second delay between batches to stay under limit
                if batch_num > 0:
                    self.stdout.write(f'  Waiting 15s to avoid rate limits...')
                    time.sleep(15)
                
                try:
                    questions_data = self.generate_batch(
                        skill, 
                        difficulty, 
                        batch_count
                    )

                    if questions_data:
                        saved_count = self.save_questions(skill, questions_data, difficulty)
                        total_generated += saved_count
                        self.stdout.write(
                            f'  [OK] Batch {batch_num + 1}/{batches} ({difficulty}): '
                            f'{saved_count}/{batch_count} questions saved'
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [WARN] Batch {batch_num + 1}/{batches} ({difficulty}): '
                                f'AI generation failed'
                            )
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  [ERROR] Batch {batch_num + 1}/{batches} ({difficulty}): {str(e)}'
                        )
                    )

        final_count = QuestionBank.objects.filter(skill=skill).count()
        self.stdout.write(
            self.style.SUCCESS(
                f'[OK] {skill.name}: {total_generated} new questions generated '
                f'(Total: {final_count}/100)'
            )
        )

    def generate_batch(self, skill, difficulty, count):
        """Generate a batch of questions for specific difficulty"""
        prompt = self.build_skill_specific_prompt(skill, difficulty, count)
        
        try:
            # Use the existing AI service
            questions_data = question_generator.generate_questions(
                skill_name=skill.name,
                skill_description=skill.description,
                difficulty=difficulty,
                count=count
            )
            return questions_data
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    AI Error: {str(e)}'))
            return None

    def build_skill_specific_prompt(self, skill, difficulty, count):
        """Build a skill-specific prompt for better question relevance"""
        category = skill.category.name if skill.category else "Technical"
        
        # Difficulty-specific guidelines
        difficulty_guides = {
            'easy': 'basic concepts, definitions, and simple applications',
            'medium': 'practical applications, problem-solving, and best practices',
            'hard': 'advanced concepts, optimization, architecture, and edge cases'
        }

        return f"""Generate {count} {difficulty} multiple-choice questions about {skill.name}.

Skill Category: {category}
Difficulty Level: {difficulty.upper()}
Focus: {difficulty_guides.get(difficulty, 'general knowledge')}

Requirements:
1. Questions must be directly relevant to {skill.name}
2. Each question should test practical knowledge
3. Include realistic scenarios and use cases
4. Provide 4 options with only ONE correct answer
5. Options should be plausible but clearly distinguishable
6. Avoid ambiguous or trick questions

Return JSON format:
[
    {{
        "question": "Question text here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Exact text of correct option",
        "difficulty": "{difficulty}",
        "points": {self.get_points_for_difficulty(difficulty)}
    }}
]"""

    def get_points_for_difficulty(self, difficulty):
        """Map difficulty to points"""
        return {
            'easy': 5,
            'medium': 10,
            'hard': 15
        }.get(difficulty, 10)

    def save_questions(self, skill, questions_data, difficulty):
        """Save generated questions to database"""
        saved_count = 0

        with transaction.atomic():
            for q_data in questions_data:
                try:
                    # Validate question data
                    if not self.validate_question_data(q_data):
                        continue

                    # Get options and correct answer
                    options = q_data.get('options', [])
                    correct_answer = q_data.get('correct_answer', '')

                    # Ensure correct answer is in options
                    if correct_answer not in options:
                        # Try to find closest match
                        correct_answer = options[0] if options else ''

                    # Create question
                    QuestionBank.objects.create(
                        skill=skill,
                        question_text=q_data.get('question', ''),
                        options=options,
                        correct_answer=correct_answer,
                        difficulty=difficulty,
                        points=self.get_points_for_difficulty(difficulty),
                        question_type='mcq',
                        explanation=q_data.get('explanation', ''),
                        is_active=True
                    )
                    saved_count += 1

                except Exception as e:
                    self.stdout.write(f'      Error saving question: {str(e)}')
                    continue

        return saved_count

    def validate_question_data(self, q_data):
        """Validate question data structure"""
        required_fields = ['question', 'options', 'correct_answer']
        
        for field in required_fields:
            if field not in q_data:
                return False

        # Check options count
        options = q_data.get('options', [])
        if not isinstance(options, list) or len(options) != 4:
            return False

        # Check question text
        if not q_data.get('question') or len(q_data.get('question', '')) < 10:
            return False

        return True
