from django.contrib import admin
from .models import Job, Application, Message

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