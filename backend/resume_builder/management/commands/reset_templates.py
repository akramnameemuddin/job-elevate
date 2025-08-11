from django.core.management.base import BaseCommand
from resume_builder.models import ResumeTemplate
from resume_builder.default_templates import DEFAULT_TEMPLATES


class Command(BaseCommand):
    help = 'Reset and reload default resume templates'

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.WARNING('Resetting resume templates...'))
            
            # Delete all existing templates
            deleted_count = ResumeTemplate.objects.count()
            ResumeTemplate.objects.all().delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Deleted {deleted_count} existing templates')
            )
            
            # Load fresh templates
            created_count = 0
            
            for template_data in DEFAULT_TEMPLATES:
                try:
                    template = ResumeTemplate.objects.create(
                        name=template_data['name'],
                        description=template_data['description'],
                        html_structure=template_data['html_structure'],
                        css_structure=template_data.get('css_structure', ''),
                    )
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created template: {template.name}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to create template {template_data["name"]}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Successfully reset templates!\n'
                    f'   Created: {created_count} templates\n'
                    f'   All templates are now ready for use!'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error resetting templates: {str(e)}')
            )
            # Don't fail the build, just warn
            self.stdout.write(
                self.style.WARNING('Template reset failed, but build will continue...')
            )
