# management/commands/create_resume_templates.py
from django.core.management.base import BaseCommand
from resume_builder.models import ResumeTemplate
from resume_builder.default_templates import DEFAULT_TEMPLATES

class Command(BaseCommand):
    help = 'Load default resume templates into the database'

    def handle(self, *args, **kwargs):
        for template_data in DEFAULT_TEMPLATES:
            ResumeTemplate.objects.update_or_create(
                name=template_data['name'],
                defaults={
                    'description': template_data['description'],
                    'html_structure': template_data['html_structure'],
                    'css_structure': template_data.get('css_structure', ''),
                    'is_active': True
                }
            )
        self.stdout.write(self.style.SUCCESS('Default resume templates loaded successfully.'))
