from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, RecruiterProfile

class CustomUserAdmin(UserAdmin):
    # Display these fields in the admin list view
    list_display = ('username', 'email', 'full_name', 'user_type', 'email_verified', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'email_verified', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'full_name', 'phone_number')
    ordering = ('-date_joined',)
    
    # Fields to display in the user detail/edit form
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': (
                'full_name', 'phone_number', 'profile_photo', 
                'linkedin_profile', 'github_profile', 'portfolio_website'
            )
        }),
        ('Email Verification', {
            'fields': ('email_verified', 'email_otp', 'otp_created_at')
        }),
        ('User Type & Career Info', {
            'fields': ('user_type', 'objective')
        }),
        ('Student Information', {
            'fields': ('university', 'degree', 'graduation_year', 'cgpa'),
            'classes': ('collapse',)
        }),
        ('Professional Information', {
            'fields': ('job_title', 'organization', 'experience', 'industry'),
            'classes': ('collapse',)
        }),
        ('Skills & Experience', {
            'fields': (
                'technical_skills', 'soft_skills', 'projects', 
                'internships', 'certifications', 'work_experience', 
                'work_experience_description', 'achievements', 
                'extracurricular_activities'
            ),
            'classes': ('collapse',)
        }),
        ('Company Information (Recruiters)', {
            'fields': ('company_name', 'company_website', 'company_description'),
            'classes': ('collapse',)
        }),
    )
    
    # Fields to display when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'user_type', 'password1', 'password2'),
        }),
    )

class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'company_website')
    search_fields = ('user__username', 'user__email', 'company_name')
    list_filter = ('user__date_joined',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Company Information', {
            'fields': ('company_name', 'company_website', 'company_description')
        }),
    )

# Register the models
admin.site.register(User, CustomUserAdmin)
admin.site.register(RecruiterProfile, RecruiterProfileAdmin)

# Customize admin site headers
admin.site.site_header = "JobElevate Administration"
admin.site.site_title = "JobElevate Admin Portal"
admin.site.index_title = "Welcome to JobElevate Administration"