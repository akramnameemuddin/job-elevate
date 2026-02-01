"""
Test Gemini API - Generate 5-10 questions to verify rate limit is reset
Usage: python manage.py test_gemini_api
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from assessments.ai_service import QuestionGeneratorService, GEMINI_AVAILABLE
import time


class Command(BaseCommand):
    help = 'Test Gemini API by generating 5-10 sample questions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skill',
            type=str,
            default='Python',
            help='Skill name to test (default: Python)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of questions to generate (default: 5)'
        )
        parser.add_argument(
            '--difficulty',
            type=str,
            default='easy',
            choices=['easy', 'medium', 'hard'],
            help='Difficulty level (default: easy)'
        )

    def handle(self, *args, **options):
        skill_name = options['skill']
        count = options['count']
        difficulty = options['difficulty']
        
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.HTTP_INFO('GEMINI API TEST'))
        self.stdout.write('=' * 70)
        
        # Step 1: Check if API is available
        self.stdout.write('\n[Step 1] Checking API availability...')
        if not GEMINI_AVAILABLE:
            self.stdout.write(self.style.ERROR('✗ Gemini API is NOT available'))
            self.stdout.write(self.style.WARNING('  Check your GOOGLE_API_KEY in .env file'))
            return
        
        self.stdout.write(self.style.SUCCESS('✓ Gemini API is available'))
        
        # Step 2: Check API key
        self.stdout.write('\n[Step 2] Checking API key...')
        api_key = getattr(settings, 'GOOGLE_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR('✗ No API key found'))
            return
        
        masked_key = api_key[:8] + '...' + api_key[-4:] if len(api_key) > 12 else '***'
        self.stdout.write(self.style.SUCCESS(f'✓ API key found: {masked_key}'))
        
        # Step 3: Initialize service
        self.stdout.write('\n[Step 3] Initializing Question Generator Service...')
        try:
            service = QuestionGeneratorService()
            if not service.ai_available:
                self.stdout.write(self.style.ERROR('✗ Service initialization failed'))
                return
            self.stdout.write(self.style.SUCCESS(f'✓ Service initialized with model: {service.model_name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
            return
        
        # Step 4: Test API with small request
        self.stdout.write('\n[Step 4] Testing API connection...')
        self.stdout.write(f'  Skill: {skill_name}')
        self.stdout.write(f'  Difficulty: {difficulty}')
        self.stdout.write(f'  Questions: {count}')
        self.stdout.write('')
        
        start_time = time.time()
        
        try:
            self.stdout.write('  Sending request to Gemini API...')
            questions = service.generate_questions(
                skill_name=skill_name,
                skill_description=f'Testing {skill_name} skill',
                difficulty=difficulty,
                count=count
            )
            
            elapsed = time.time() - start_time
            
            if not questions or len(questions) == 0:
                self.stdout.write(self.style.ERROR(f'✗ No questions generated'))
                self.stdout.write(self.style.WARNING(f'  Time taken: {elapsed:.2f}s'))
                self.stdout.write(self.style.WARNING('  Possible reasons:'))
                self.stdout.write('    - Rate limit still active')
                self.stdout.write('    - API error')
                self.stdout.write('    - Invalid API key')
                return
            
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully generated {len(questions)} questions!'))
            self.stdout.write(f'  Time taken: {elapsed:.2f}s')
            
            # Step 5: Display generated questions
            self.stdout.write('\n[Step 5] Generated Questions:')
            self.stdout.write('=' * 70)
            
            for i, q in enumerate(questions, 1):
                self.stdout.write(f'\n{self.style.HTTP_INFO(f"Question {i}:")}')
                
                # Show full question text
                question_text = q.get("question", q.get("question_text", "N/A"))
                if len(question_text) > 150:
                    self.stdout.write(f'  Q: {question_text[:150]}...')
                else:
                    self.stdout.write(f'  Q: {question_text}')
                
                self.stdout.write(f'  Difficulty: {q.get("difficulty", "N/A")}')
                self.stdout.write(f'  Points: {q.get("points", q.get("point_value", "N/A"))}')
                
                # Show all options
                options = q.get("options", [])
                self.stdout.write(f'  Options ({len(options)} choices):')
                for opt in options:
                    prefix = '    ➜' if opt == q.get("correct_answer") else '    •'
                    if len(opt) > 60:
                        self.stdout.write(f'{prefix} {opt[:60]}...')
                    else:
                        self.stdout.write(f'{prefix} {opt}')
                
                correct = q.get("correct_answer", "N/A")
                self.stdout.write(f'  ✓ Correct: {correct[:80] if len(correct) > 80 else correct}')
            
            # Step 6: Success summary
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(self.style.SUCCESS('TEST PASSED! ✓'))
            self.stdout.write('=' * 70)
            self.stdout.write(self.style.SUCCESS('Your Gemini API is working correctly!'))
            self.stdout.write(f'You can now generate questions for your skills.')
            self.stdout.write('')
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.stdout.write(self.style.ERROR(f'\n✗ API Request Failed'))
            self.stdout.write(f'  Time taken: {elapsed:.2f}s')
            self.stdout.write(f'  Error: {str(e)[:200]}')
            
            # Check for specific errors
            error_str = str(e).lower()
            
            if '429' in error_str or 'resource_exhausted' in error_str or 'quota' in error_str:
                self.stdout.write('\n' + self.style.WARNING('RATE LIMIT ERROR'))
                self.stdout.write('  Your free tier quota is still exhausted.')
                self.stdout.write('  Solutions:')
                self.stdout.write('    1. Wait 24 hours from last usage')
                self.stdout.write('    2. Check quota: https://ai.google.dev/gemini-api/docs/quota')
                self.stdout.write('    3. Use template questions (no API needed)')
                self.stdout.write('    4. Upgrade to paid tier ($15/month)')
                
            elif '404' in error_str or 'not found' in error_str:
                self.stdout.write('\n' + self.style.WARNING('MODEL NOT FOUND'))
                self.stdout.write('  The Gemini model may not be available.')
                self.stdout.write(f'  Current model: {service.model_name}')
                self.stdout.write('  Try: gemini-1.5-flash or gemini-1.5-pro')
                
            elif '401' in error_str or 'unauthorized' in error_str or 'invalid' in error_str:
                self.stdout.write('\n' + self.style.WARNING('AUTHENTICATION ERROR'))
                self.stdout.write('  Your API key may be invalid.')
                self.stdout.write('  Generate new key: https://aistudio.google.com/app/apikey')
                
            else:
                self.stdout.write('\n' + self.style.WARNING('UNKNOWN ERROR'))
                self.stdout.write('  Check your internet connection')
                self.stdout.write('  Verify API key is correct')
            
            self.stdout.write('')
