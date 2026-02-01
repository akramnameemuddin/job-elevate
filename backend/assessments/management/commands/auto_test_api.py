"""
Auto-retry API test - waits for quota reset then tests
Usage: python manage.py auto_test_api
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import time
import datetime
import re


class Command(BaseCommand):
    help = 'Auto-retry API test after quota reset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-wait',
            type=int,
            default=120,
            help='Maximum seconds to wait (default: 120)'
        )

    def handle(self, *args, **options):
        max_wait = options['max_wait']
        
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.HTTP_INFO('AUTO-RETRY API TEST'))
        self.stdout.write('=' * 70)
        
        api_key = getattr(settings, 'GOOGLE_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR('\nNo API key found'))
            return
        
        masked_key = api_key[:8] + '...' + api_key[-4:]
        self.stdout.write(f'\nAPI Key: {masked_key}')
        
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        attempt = 0
        max_attempts = 3
        
        while attempt < max_attempts:
            attempt += 1
            self.stdout.write(f'\n[Attempt {attempt}/{max_attempts}] Testing API...')
            
            try:
                response = model.generate_content('Say "API is working!"')
                
                # Success!
                self.stdout.write('\n' + '=' * 70)
                self.stdout.write(self.style.SUCCESS('✓ SUCCESS! API IS WORKING!'))
                self.stdout.write('=' * 70)
                self.stdout.write(f'\nResponse: {response.text}')
                self.stdout.write(f'\nTime: {datetime.datetime.now().strftime("%I:%M:%S %p")}')
                
                # Test question generation
                self.stdout.write('\n\nTesting question generation (3 questions)...')
                try:
                    from assessments.ai_service import QuestionGeneratorService
                    service = QuestionGeneratorService()
                    questions = service.generate_questions('Python', 'Programming language', 'easy', 3)
                    
                    if questions:
                        self.stdout.write(self.style.SUCCESS(f'\n✓ Generated {len(questions)} questions!'))
                        for i, q in enumerate(questions, 1):
                            self.stdout.write(f'\n{i}. {q.get("question", "N/A")[:80]}...')
                    else:
                        self.stdout.write(self.style.WARNING('\nNo questions generated'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'\nQuestion generation error: {str(e)[:100]}'))
                
                self.stdout.write('\n' + '=' * 70)
                self.stdout.write(self.style.SUCCESS('QUOTA RESET CONFIRMED ✓'))
                self.stdout.write('=' * 70)
                self.stdout.write('\nYou can now:')
                self.stdout.write('  • Generate questions for skills')
                self.stdout.write('  • Run: python manage.py test_gemini_api')
                self.stdout.write('  • Use AI as fallback for new skills')
                return
                
            except Exception as e:
                error_msg = str(e)
                
                if '429' in error_msg or 'quota' in error_msg.lower():
                    # Extract wait time
                    wait_seconds = None
                    match = re.search(r'retry in ([\d.]+)s', error_msg)
                    if match:
                        wait_seconds = float(match.group(1))
                    
                    if wait_seconds and wait_seconds <= max_wait:
                        self.stdout.write(self.style.WARNING(f'\n⏳ Rate limited. Waiting {int(wait_seconds)}s...'))
                        
                        # Countdown
                        for remaining in range(int(wait_seconds), 0, -10):
                            if remaining <= 10:
                                self.stdout.write(f'   {remaining}s...', ending='')
                            else:
                                self.stdout.write(f'   {remaining}s...', ending='')
                            time.sleep(min(10, remaining))
                        
                        self.stdout.write('\n   Retrying...')
                        continue
                    elif wait_seconds:
                        self.stdout.write(self.style.ERROR(f'\n✗ Wait time too long: {int(wait_seconds)}s (max: {max_wait}s)'))
                        self.stdout.write(f'\nTry again in {int(wait_seconds/60)} minutes')
                        return
                    else:
                        self.stdout.write(self.style.ERROR('\n✗ Rate limited (no wait time specified)'))
                        self.stdout.write('\nTry again later or use templates')
                        return
                else:
                    self.stdout.write(self.style.ERROR(f'\n✗ Error: {error_msg[:150]}'))
                    return
        
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.ERROR('FAILED AFTER 3 ATTEMPTS'))
        self.stdout.write('=' * 70)
        self.stdout.write('\nRecommendation: Use template questions')
        self.stdout.write('You have 708 questions ready for 21 skills')
