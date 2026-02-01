from django.contrib import admin
from .models import Course, SkillGap, LearningPath, LearningPathCourse, CourseProgress


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'skill', 'difficulty_level', 'platform', 'duration_weeks', 
                    'target_proficiency_level', 'rating', 'is_free', 'is_active')
    list_filter = ('difficulty_level', 'platform', 'course_type', 'is_free', 'is_active', 'skill__category')
    search_fields = ('title', 'description', 'instructor', 'skill__name')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Course Information', {
            'fields': ('title', 'description', 'skill', 'course_type', 'difficulty_level')
        }),
        ('Platform & Access', {
            'fields': ('platform', 'url', 'is_free', 'price')
        }),
        ('Duration & Expectations', {
            'fields': ('duration_hours', 'duration_weeks', 'target_proficiency_level')
        }),
        ('Metadata', {
            'fields': ('instructor', 'thumbnail', 'rating', 'is_active')
        }),
    )


@admin.register(SkillGap)
class SkillGapAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'current_level', 'required_level', 'gap_value', 
                    'priority', 'target_job_title', 'is_addressed', 'identified_at')
    list_filter = ('priority', 'is_addressed', 'skill__category', 'identified_at')
    search_fields = ('user__username', 'user__email', 'skill__name', 'target_job_title')
    date_hierarchy = 'identified_at'
    list_editable = ('is_addressed',)
    readonly_fields = ('gap_value', 'identified_at')
    
    fieldsets = (
        ('Gap Information', {
            'fields': ('user', 'skill', 'target_job_title')
        }),
        ('Skill Levels', {
            'fields': ('current_level', 'required_level', 'gap_value', 'priority')
        }),
        ('Status', {
            'fields': ('is_addressed', 'identified_at')
        }),
    )


class LearningPathCourseInline(admin.TabularInline):
    model = LearningPathCourse
    extra = 1
    fields = ('course', 'order', 'is_completed', 'completed_at')
    ordering = ('order',)


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'skill_gap', 'status', 'progress_percentage', 
                    'estimated_weeks', 'started_at', 'completed_at')
    list_filter = ('status', 'skill_gap__skill__category', 'created_at')
    search_fields = ('title', 'description', 'user__username', 'skill_gap__skill__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('progress_percentage', 'started_at', 'completed_at', 'created_at', 'updated_at')
    inlines = [LearningPathCourseInline]
    
    fieldsets = (
        ('Path Information', {
            'fields': ('user', 'skill_gap', 'title', 'description')
        }),
        ('Timeline', {
            'fields': ('estimated_weeks', 'estimated_hours', 'status')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'started_at', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LearningPathCourse)
class LearningPathCourseAdmin(admin.ModelAdmin):
    list_display = ('learning_path', 'course', 'order', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'learning_path__status')
    search_fields = ('learning_path__title', 'course__title', 'learning_path__user__username')
    ordering = ('learning_path', 'order')


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'progress_percentage', 
                    'time_spent_hours', 'certificate_earned', 'last_accessed_at')
    list_filter = ('status', 'certificate_earned', 'course__skill__category', 'enrolled_at')
    search_fields = ('user__username', 'user__email', 'course__title')
    date_hierarchy = 'enrolled_at'
    readonly_fields = ('enrolled_at', 'started_at', 'completed_at', 'last_accessed_at')
    
    fieldsets = (
        ('Progress Information', {
            'fields': ('user', 'course', 'learning_path', 'status')
        }),
        ('Progress Details', {
            'fields': ('progress_percentage', 'time_spent_hours')
        }),
        ('Timeline', {
            'fields': ('enrolled_at', 'started_at', 'completed_at', 'last_accessed_at')
        }),
        ('Certificate', {
            'fields': ('certificate_earned', 'certificate_url')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
