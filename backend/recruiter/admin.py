from django.contrib import admin
from .models import Job, Application, Message, JobSkillRequirement, UserJobFitScore

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'job_type', 'status', 'posted_by', 'created_at')
    list_filter = ('status', 'job_type', 'created_at')
    search_fields = ('title', 'company', 'description')
    date_hierarchy = 'created_at'

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'status', 'match_score', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('applicant__full_name', 'job__title')
    date_hierarchy = 'applied_at'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'is_read', 'sent_at')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('sender__full_name', 'recipient__full_name', 'subject', 'content')
    date_hierarchy = 'sent_at'


@admin.register(JobSkillRequirement)
class JobSkillRequirementAdmin(admin.ModelAdmin):
    list_display = ('job', 'skill', 'required_proficiency', 'criticality', 'is_mandatory', 'weight')
    list_filter = ('is_mandatory', 'criticality')
    search_fields = ('job__title', 'skill__name')
    list_editable = ('required_proficiency', 'criticality', 'is_mandatory')
    ordering = ('-criticality', '-required_proficiency')


@admin.register(UserJobFitScore)
class UserJobFitScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'overall_score', 'is_good_match', 'critical_gaps_count', 'calculated_at')
    list_filter = ('is_good_match', 'calculated_at')
    search_fields = ('user__username', 'job__title')
    readonly_fields = ('overall_score', 'skill_match_score', 'experience_score', 
                      'matched_skills_count', 'total_required_skills', 'calculated_at')
    ordering = ('-overall_score',)