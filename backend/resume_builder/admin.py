from django.contrib import admin
from .models import ResumeTemplate, Resume, TailoredResume

@admin.register(ResumeTemplate)
class ResumeTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    fieldsets = (
        ('Template Info', {
            'fields': ('name', 'description', 'preview_image')
        }),
        ('Template Code', {
            'fields': ('html_structure', 'css_structure')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'template', 'status', 'created_at', 'download_count')
    list_filter = ('status', 'template', 'show_contact', 'show_skills', 'show_experience')
    search_fields = ('title', 'user__username', 'user__full_name')
    readonly_fields = ('created_at', 'updated_at', 'last_downloaded', 'download_count')
    
    fieldsets = (
        ('Resume Info', {
            'fields': ('user', 'template', 'title', 'status')
        }),
        ('Styling Options', {
            'fields': ('primary_color', 'secondary_color', 'font_family')
        }),
        ('Section Visibility', {
            'fields': (
                'show_contact', 'show_links', 'show_objective', 
                'show_education', 'show_skills', 'show_experience',
                'show_projects', 'show_certifications', 'show_achievements',
                'show_extracurricular'
            )
        }),
        ('PDF & Statistics', {
            'fields': ('pdf_file', 'created_at', 'updated_at', 'last_downloaded', 'download_count')
        }),
    )


@admin.register(TailoredResume)
class TailoredResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'match_score_before', 'match_score_after', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__full_name', 'job__title')
    readonly_fields = ('created_at', 'updated_at')