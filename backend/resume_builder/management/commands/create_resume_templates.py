# management/commands/create_resume_templates.py
from django.core.management.base import BaseCommand
from resume_builder.models import ResumeTemplate
from resume_builder.default_templates import DEFAULT_TEMPLATES

class Command(BaseCommand):
    help = 'Load default resume templates into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing templates',
        )

    def handle(self, *args, **options):
        force_update = options['force']
        
        self.stdout.write(self.style.SUCCESS('Loading default resume templates...'))
        
        created_count = 0
        updated_count = 0
        
        for template_data in DEFAULT_TEMPLATES:
            template, created = ResumeTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'description': template_data['description'],
                    'html_structure': template_data['html_structure'],
                    'css_structure': template_data.get('css_structure', ''),
                    'is_default': True,
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created template: {template.name}')
                )
            elif force_update:
                template.description = template_data['description']
                template.html_structure = template_data['html_structure']
                template.css_structure = template_data.get('css_structure', '')
                template.is_default = True
                template.is_active = True
                template.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Template already exists: {template.name} (use --force to update)')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Summary:\n'
                f'   Created: {created_count} templates\n'
                f'   Updated: {updated_count} templates\n'
                f'   Total available: {len(DEFAULT_TEMPLATES)} templates'
            )
        )
        
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS('🎉 Templates are now ready for use!')
            )
