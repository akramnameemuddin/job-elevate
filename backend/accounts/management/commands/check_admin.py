from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Check admin user status'

    def handle(self, *args, **options):
        # Check for admin users
        admins = User.objects.filter(is_superuser=True)
        
        if not admins.exists():
            self.stdout.write(
                self.style.ERROR('No admin users found!')
            )
            self.stdout.write(
                self.style.SUCCESS('Run: python manage.py create_admin')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {admins.count()} admin user(s):')
        )
        
        for admin in admins:
            self.stdout.write(f'  - Username: {admin.username}')
            self.stdout.write(f'    Email: {admin.email}')
            self.stdout.write(f'    Active: {admin.is_active}')
            self.stdout.write(f'    Staff: {admin.is_staff}')
            self.stdout.write(f'    Superuser: {admin.is_superuser}')
            self.stdout.write(f'    Date Joined: {admin.date_joined}')
            self.stdout.write('---')
        
        self.stdout.write(
            self.style.SUCCESS('Admin panel URL: /admin/')
        )
