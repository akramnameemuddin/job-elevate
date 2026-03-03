"""
Management command: reset_templates

Force-overwrites all resume templates in the database with the canonical
versions defined in resume_builder/default_templates.py.

Usage:
    python manage.py reset_templates
"""
from django.core.management.base import BaseCommand
from resume_builder.models import ResumeTemplate
from resume_builder.default_templates import DEFAULT_TEMPLATES


class Command(BaseCommand):
    help = 'Force-reset all resume templates to the canonical defaults'

    def handle(self, *args, **options):
        self.stdout.write('Resetting resume templates to canonical defaults...\n')

        updated_count = 0
        created_count = 0

        for tpl in DEFAULT_TEMPLATES:
            obj, created = ResumeTemplate.objects.update_or_create(
                name=tpl['name'],
                defaults={
                    'description': tpl.get('description', ''),
                    'html_structure': tpl['html_structure'],
                    'css_structure': tpl.get('css_structure', ''),
                    'is_active': True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created : {obj.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'  Updated : {obj.name}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Created {created_count}, updated {updated_count} template(s).'
            )
        )
