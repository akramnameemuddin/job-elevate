"""
Quick API Status Checker
Usage: python manage.py check_api_status
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import datetime


class Command(BaseCommand):
    help = 'Check Gemini API quota status'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.HTTP_INFO('GEMINI API STATUS CHECK'))
        self.stdout.write('=' * 70)
        
        # Check API key
        api_key = getattr(settings, 'GOOGLE_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR('\n✗ No API key configured'))
            return
        
        masked_key = api_key[:8] + '...' + api_key[-4:]
        self.stdout.write(f'\nAPI Key: {masked_key}')
        
        # Try a minimal API call
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            model_name = 'models/gemini-2.5-flash'
            
            self.stdout.write(f'\nTesting API with {model_name}...\n')
            
            response = client.models.generate_content(
                model=model_name,
                contents='Say hello'
            )
            
            if response and response.text:
                self.stdout.write(self.style.SUCCESS('✓ API IS WORKING!'))
                self.stdout.write(f'Response: {response.text[:100]}')
                self.stdout.write('\n' + '=' * 70)
                self.stdout.write(self.style.SUCCESS('STATUS: RATE LIMIT RESET ✓'))
                self.stdout.write('=' * 70)
                self.stdout.write('You can now generate questions!')
                
        except Exception as e:
            error_msg = str(e)
            
            self.stdout.write(self.style.ERROR('\n✗ API REQUEST FAILED'))
            self.stdout.write(f'\nError: {error_msg[:300]}\n')
            
            if '429' in error_msg or 'quota' in error_msg.lower():
                self.stdout.write('=' * 70)
                self.stdout.write(self.style.WARNING('STATUS: RATE LIMIT ACTIVE ✗'))
                self.stdout.write('=' * 70)
                
                # Extract retry time if available
                if 'retry in' in error_msg.lower():
                    import re
                    match = re.search(r'retry in ([\d.]+)s', error_msg)
                    if match:
                        wait_seconds = float(match.group(1))
                        wait_time = datetime.timedelta(seconds=wait_seconds)
                        self.stdout.write(f'\nWait Time: {wait_time}')
                        estimated_time = datetime.datetime.now() + wait_time
                        self.stdout.write(f'Try Again After: {estimated_time.strftime("%I:%M %p")}')
                
                self.stdout.write('\n📊 FREE TIER LIMITS:')
                self.stdout.write('  • Requests: 20 per day per model')
                self.stdout.write('  • Tokens: Limited per minute')
                self.stdout.write('  • Resets: Every 24 hours')
                
                self.stdout.write('\n💡 YOUR OPTIONS:')
                self.stdout.write('  1. ⏰ Wait for rate limit to reset')
                self.stdout.write('  2. 📝 Use template questions (708 available)')
                self.stdout.write('  3. 🔑 Try a different API key')
                self.stdout.write('  4. 💳 Upgrade to paid tier ($15/month)')
                
                self.stdout.write('\n🔗 USEFUL LINKS:')
                self.stdout.write('  • Check usage: https://ai.google.dev/gemini-api/docs/quota')
                self.stdout.write('  • Get new key: https://aistudio.google.com/app/apikey')
                self.stdout.write('  • Pricing: https://ai.google.dev/pricing')
                
            elif '404' in error_msg:
                self.stdout.write(self.style.WARNING('\nMODEL NOT FOUND'))
                self.stdout.write('The gemini-2.0-flash-exp model may not be available.')
                self.stdout.write('Try: gemini-1.5-flash or gemini-1.5-pro')
                
            elif '401' in error_msg or 'unauthorized' in error_msg.lower():
                self.stdout.write(self.style.WARNING('\nINVALID API KEY'))
                self.stdout.write('Generate a new key: https://aistudio.google.com/app/apikey')
        
        self.stdout.write('\n' + '=' * 70)
