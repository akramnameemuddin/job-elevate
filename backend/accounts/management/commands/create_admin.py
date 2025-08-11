from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser for deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Admin username',
            default=None
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Admin email',
            default=None
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Admin password',
            default=None
        )

    def handle(self, *args, **options):
        # Get credentials from options, environment variables, or use defaults
        username = (
            options['username'] or 
            os.environ.get('ADMIN_USERNAME') or 
            'admin'
        )
        email = (
            options['email'] or 
            os.environ.get('ADMIN_EMAIL') or 
            'admin@jobelevate.com'
        )
        password = (
            options['password'] or 
            os.environ.get('ADMIN_PASSWORD') or 
            'JobElevate2025!'
        )
        
        # Check if superuser already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Superuser "{username}" already exists. Skipping creation.'
                )
            )
            return
        
        # Check if any superuser exists
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING(
                    'A superuser already exists. Skipping creation.'
                )
            )
            return
        
        try:
            # Create the superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                user_type='admin',  # Set user type to admin
                first_name='System',
                last_name='Administrator'
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created superuser: {username}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Email: {email}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    'Use these credentials to access the admin panel at /admin/'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error creating superuser: {str(e)}'
                )
            )
