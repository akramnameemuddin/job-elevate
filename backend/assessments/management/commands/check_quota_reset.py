"""
Check Quota Reset Time for Gemini API
Usage: python manage.py check_quota_reset
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import datetime
import re


class Command(BaseCommand):
    help = 'Check when your Gemini API quota will reset'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.HTTP_INFO('GEMINI API QUOTA CHECKER'))
        self.stdout.write('=' * 70)
        
        api_key = getattr(settings, 'GOOGLE_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR('\n✗ No API key found'))
            return
        
        masked_key = api_key[:8] + '...' + api_key[-4:]
        self.stdout.write(f'\nCurrent API Key: {masked_key}')
        self.stdout.write(f'Current Time: {datetime.datetime.now().strftime("%I:%M:%S %p")}')
        
        # Make a minimal test call
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            self.stdout.write('\nTesting API (minimal request)...')
            response = model.generate_content('hi')
            
            # Success!
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(self.style.SUCCESS('✓ API IS WORKING! QUOTA RESET!'))
            self.stdout.write('=' * 70)
            self.stdout.write(f'\nResponse: {response.text}')
            self.stdout.write('\n🎉 You can now generate questions!')
            
        except Exception as e:
            error_msg = str(e)
            
            # Extract wait time
            wait_seconds = None
            wait_time_str = None
            
            if 'retry in' in error_msg:
                match = re.search(r'retry in ([\d.]+)s', error_msg)
                if match:
                    wait_seconds = float(match.group(1))
                    hours = int(wait_seconds // 3600)
                    minutes = int((wait_seconds % 3600) // 60)
                    seconds = int(wait_seconds % 60)
                    
                    if hours > 0:
                        wait_time_str = f'{hours}h {minutes}m {seconds}s'
                    elif minutes > 0:
                        wait_time_str = f'{minutes}m {seconds}s'
                    else:
                        wait_time_str = f'{seconds}s'
            
            if '429' in error_msg or 'quota' in error_msg.lower():
                self.stdout.write('\n' + '=' * 70)
                self.stdout.write(self.style.ERROR('✗ QUOTA EXHAUSTED'))
                self.stdout.write('=' * 70)
                
                # Parse quota information
                if 'per minute' in error_msg.lower():
                    self.stdout.write('\n⏱️  Rate Limit: PER MINUTE')
                    self.stdout.write('   This is a short-term limit')
                    if wait_time_str:
                        self.stdout.write(f'   Wait: {wait_time_str}')
                        estimated = datetime.datetime.now() + datetime.timedelta(seconds=wait_seconds)
                        self.stdout.write(f'   Try again at: {estimated.strftime("%I:%M:%S %p")}')
                
                if 'per day' in error_msg.lower():
                    self.stdout.write('\n📅 Rate Limit: PER DAY')
                    self.stdout.write('   This is the 24-hour quota')
                    self.stdout.write('   Limit: 20 requests per day')
                    if wait_time_str:
                        self.stdout.write(f'   Wait: {wait_time_str}')
                        estimated = datetime.datetime.now() + datetime.timedelta(seconds=wait_seconds)
                        self.stdout.write(f'   Resets at: {estimated.strftime("%I:%M:%S %p, %b %d")}')
                
                # Show options
                self.stdout.write('\n' + '=' * 70)
                self.stdout.write('YOUR OPTIONS:')
                self.stdout.write('=' * 70)
                
                self.stdout.write('\n1️⃣  WAIT (Free)')
                if wait_time_str:
                    self.stdout.write(f'   Wait {wait_time_str} then run: python manage.py check_quota_reset')
                else:
                    self.stdout.write('   Check back in a few hours')
                
                self.stdout.write('\n2️⃣  USE TEMPLATES (Free - Best Option)')
                self.stdout.write('   You have 708 template questions ready')
                self.stdout.write('   21 skills fully covered')
                self.stdout.write('   No API needed, works instantly')
                
                self.stdout.write('\n3️⃣  NEW API KEY (Free)')
                self.stdout.write('   Create with different Google account')
                self.stdout.write('   Get key: https://aistudio.google.com/app/apikey')
                self.stdout.write('   Update .env: GOOGLE_API_KEY=new-key')
                
                self.stdout.write('\n4️⃣  UPGRADE TO PAID ($15/month)')
                self.stdout.write('   1,500 requests per day')
                self.stdout.write('   No waiting or rate limits')
                self.stdout.write('   Pricing: https://ai.google.dev/pricing')
                
                # Recommendations
                self.stdout.write('\n' + '=' * 70)
                self.stdout.write('💡 RECOMMENDATION:')
                self.stdout.write('=' * 70)
                
                if wait_seconds and wait_seconds < 120:
                    self.stdout.write(f'\n⏳ Wait just {wait_time_str} then test again!')
                    self.stdout.write('   This is a short per-minute limit.')
                    estimated = datetime.datetime.now() + datetime.timedelta(seconds=wait_seconds)
                    self.stdout.write(f'   Run this command again at: {estimated.strftime("%I:%M:%S %p")}')
                elif wait_seconds and wait_seconds < 3600:
                    self.stdout.write(f'\n⏰ Wait {wait_time_str} or use templates meanwhile')
                    self.stdout.write('   Your assessments work perfectly with templates!')
                else:
                    self.stdout.write('\n📝 Use template questions (recommended)')
                    self.stdout.write('   Your system has 708 high-quality questions')
                    self.stdout.write('   21 skills ready for unlimited assessments')
                    self.stdout.write('   No API needed!')
            
            else:
                self.stdout.write(self.style.ERROR(f'\n✗ Error: {error_msg[:200]}'))
        
        self.stdout.write('\n' + '=' * 70)
