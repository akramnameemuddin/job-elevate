"""
Management command to clean up duplicate skills in the database.
This command will merge duplicate skills (case-insensitive) keeping the first one.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from assessments.models import Skill, UserSkillProfile, QuestionBank
from recruiter.models import JobSkillRequirement
from learning.models import SkillGap


class Command(BaseCommand):
    help = 'Remove duplicate skills (case-insensitive) and merge their data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find duplicate skills (case-insensitive)
        all_skills = Skill.objects.all().order_by('id')
        skill_names = {}
        duplicates = []
        
        for skill in all_skills:
            name_lower = skill.name.lower()
            if name_lower in skill_names:
                duplicates.append({
                    'original': skill_names[name_lower],
                    'duplicate': skill,
                    'name': skill.name
                })
            else:
                skill_names[name_lower] = skill
        
        if not duplicates:
            self.stdout.write(self.style.SUCCESS('✓ No duplicate skills found!'))
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'\nFound {len(duplicates)} duplicate skill(s):'
            )
        )
        
        for dup in duplicates:
            self.stdout.write(
                f"  - '{dup['duplicate'].name}' (ID: {dup['duplicate'].id}) "
                f"duplicates '{dup['original'].name}' (ID: {dup['original'].id})"
            )
        
        if dry_run:
            self.stdout.write('\nDRY RUN - Would merge these duplicates')
            return
        
        # Ask for confirmation
        confirm = input('\nDo you want to merge these duplicates? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.ERROR('Operation cancelled'))
            return
        
        # Merge duplicates
        with transaction.atomic():
            for dup in duplicates:
                original = dup['original']
                duplicate = dup['duplicate']
                
                self.stdout.write(
                    f"\nMerging '{duplicate.name}' (ID: {duplicate.id}) "
                    f"into '{original.name}' (ID: {original.id})..."
                )
                
                # Update UserSkillProfile
                profile_count = UserSkillProfile.objects.filter(skill=duplicate).count()
                if profile_count > 0:
                    UserSkillProfile.objects.filter(skill=duplicate).update(skill=original)
                    self.stdout.write(f"  - Updated {profile_count} user skill profile(s)")
                
                # Update QuestionBank
                question_count = QuestionBank.objects.filter(skill=duplicate).count()
                if question_count > 0:
                    QuestionBank.objects.filter(skill=duplicate).update(skill=original)
                    self.stdout.write(f"  - Updated {question_count} question(s)")
                
                # Update JobSkillRequirement
                job_req_count = JobSkillRequirement.objects.filter(skill=duplicate).count()
                if job_req_count > 0:
                    # Need to handle potential duplicates after merge
                    job_reqs = JobSkillRequirement.objects.filter(skill=duplicate)
                    for req in job_reqs:
                        # Check if original already has requirement for this job
                        existing = JobSkillRequirement.objects.filter(
                            job=req.job,
                            skill=original
                        ).first()
                        
                        if existing:
                            # Keep the one with higher proficiency requirement
                            if req.required_proficiency > existing.required_proficiency:
                                existing.required_proficiency = req.required_proficiency
                                existing.criticality = req.criticality
                                existing.is_mandatory = req.is_mandatory
                                existing.skill_type = req.skill_type
                                existing.weight = req.weight
                                existing.description = req.description
                                existing.save()
                            req.delete()
                        else:
                            req.skill = original
                            req.save()
                    
                    self.stdout.write(f"  - Updated {job_req_count} job requirement(s)")
                
                # Update SkillGap
                try:
                    gap_count = SkillGap.objects.filter(skill=duplicate).count()
                    if gap_count > 0:
                        SkillGap.objects.filter(skill=duplicate).update(skill=original)
                        self.stdout.write(f"  - Updated {gap_count} skill gap(s)")
                except:
                    pass  # SkillGap might not exist
                
                # Delete the duplicate
                duplicate.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Deleted duplicate skill '{duplicate.name}' (ID: {duplicate.id})"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully merged {len(duplicates)} duplicate skill(s)!'
            )
        )
        
        # Show final count
        final_count = Skill.objects.count()
        self.stdout.write(f'\nTotal skills in database: {final_count}')
