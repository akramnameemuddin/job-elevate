"""
Comprehensive Django Admin for Assessments App
Feature-rich admin interface with filters, actions, inline editing, and analytics
"""
from django.contrib import admin
from django.db.models import Count, Avg, Q, F
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from .models import (
    SkillCategory, Skill, QuestionBank, Assessment, Question,
    AssessmentAttempt, UserAnswer, UserSkillScore, UserSkillProfile
)


# ============================================================================
# INLINE ADMINS
# ============================================================================

class SkillInline(admin.TabularInline):
    """Inline for Skills under SkillCategory"""
    model = Skill
    extra = 0
    fields = ('name', 'is_active', 'questions_generated', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True


class QuestionBankInline(admin.TabularInline):
    """Inline for QuestionBank under Skill"""
    model = QuestionBank
    extra = 0
    fields = ('question_text_short', 'difficulty', 'points', 'success_rate_display', 'times_used')
    readonly_fields = ('question_text_short', 'success_rate_display', 'times_used')
    show_change_link = True
    max_num = 10
    
    def question_text_short(self, obj):
        return obj.question_text[:80] + '...' if len(obj.question_text) > 80 else obj.question_text
    question_text_short.short_description = 'Question'
    
    def success_rate_display(self, obj):
        rate = obj.success_rate
        color = 'green' if rate >= 70 else 'orange' if rate >= 50 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, f'{rate:.1f}%'
        )
    success_rate_display.short_description = 'Success Rate'


class UserAnswerInline(admin.TabularInline):
    """Inline for UserAnswers under AssessmentAttempt"""
    model = UserAnswer
    extra = 0
    fields = ('question_display', 'selected_answer_short', 'is_correct', 'points_earned', 'time_taken_seconds')
    readonly_fields = ('question_display', 'selected_answer_short', 'is_correct', 'points_earned')
    show_change_link = True
    max_num = 20
    
    def question_display(self, obj):
        if obj.question_bank:
            return obj.question_bank.question_text[:50] + '...'
        return 'N/A'
    question_display.short_description = 'Question'
    
    def selected_answer_short(self, obj):
        answer = obj.selected_answer[:50]
        color = 'green' if obj.is_correct else 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, answer
        )
    selected_answer_short.short_description = 'Answer'


# ============================================================================
# MODEL ADMINS
# ============================================================================

@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    """Admin for SkillCategory with inline skills"""
    list_display = ('name', 'skills_count', 'icon', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    inlines = [SkillInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'icon')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def skills_count(self, obj):
        count = obj.skills.count()
        url = reverse('admin:assessments_skill_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} skills</a>', url, count)
    skills_count.short_description = 'Skills'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(skills_count=Count('skills'))


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Admin for Skill with question generation tracking"""
    list_display = (
        'name', 'category', 'is_active', 'questions_count', 
        'questions_status', 'questions_generated_at', 'attempts_count'
    )
    list_filter = (
        'is_active', 'questions_generated', 'category', 'created_at'
    )
    search_fields = ('name', 'description', 'category__name')
    readonly_fields = ('questions_generated_at', 'created_at', 'updated_at', 'questions_stats')
    inlines = [QuestionBankInline]
    actions = ['mark_questions_needed', 'activate_skills', 'deactivate_skills']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'description', 'is_active')
        }),
        ('Question Generation Status', {
            'fields': ('questions_generated', 'questions_generated_at', 'questions_stats')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def questions_count(self, obj):
        count = obj.question_bank.count()
        url = reverse('admin:assessments_questionbank_changelist') + f'?skill__id__exact={obj.id}'
        color = 'green' if count >= 20 else 'orange' if count >= 10 else 'red'
        return format_html(
            '<a href="{}" style="color: {}; font-weight: bold;">{}</a>',
            url, color, count
        )
    questions_count.short_description = 'Questions'
    
    def questions_status(self, obj):
        count = obj.question_bank.count()
        if count >= 20:
            return format_html('<span style="color: green;">✓ Ready ({}/20+)</span>', count)
        elif count > 0:
            return format_html('<span style="color: orange;">⚠ Partial ({}/20)</span>', count)
        else:
            return format_html('<span style="color: red;">✗ No questions</span>')
    questions_status.short_description = 'Status'
    
    def attempts_count(self, obj):
        count = obj.attempts.count()
        if count > 0:
            url = reverse('admin:assessments_assessmentattempt_changelist') + f'?skill__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return '0'
    attempts_count.short_description = 'Attempts'
    
    def questions_stats(self, obj):
        """Display detailed question statistics"""
        questions = obj.question_bank.all()
        if not questions:
            return format_html('<span style="color: red;">No questions available</span>')
        
        easy = questions.filter(difficulty='easy').count()
        medium = questions.filter(difficulty='medium').count()
        hard = questions.filter(difficulty='hard').count()
        ai_generated = questions.filter(created_by_ai=True).count()
        template = questions.filter(created_by_ai=False).count()
        
        total_used = sum(q.times_used for q in questions)
        avg_success = sum(q.success_rate for q in questions) / questions.count() if questions else 0
        
        return format_html(
            '<strong>Total:</strong> {}<br>'
            '<strong>Easy:</strong> {} | <strong>Medium:</strong> {} | <strong>Hard:</strong> {}<br>'
            '<strong>AI Generated:</strong> {} | <strong>Template:</strong> {}<br>'
            '<strong>Total Used:</strong> {} | <strong>Avg Success:</strong> {}',
            questions.count(), easy, medium, hard, ai_generated, template, total_used, f'{avg_success:.1f}%'
        )
    questions_stats.short_description = 'Question Statistics'
    
    def mark_questions_needed(self, request, queryset):
        updated = queryset.update(questions_generated=False)
        self.message_user(request, f'{updated} skill(s) marked as needing questions.')
    mark_questions_needed.short_description = 'Mark as needing questions'
    
    def activate_skills(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} skill(s) activated.')
    activate_skills.short_description = 'Activate selected skills'
    
    def deactivate_skills(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} skill(s) deactivated.')
    deactivate_skills.short_description = 'Deactivate selected skills'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category').annotate(
            questions_count=Count('question_bank'),
            attempts_count=Count('attempts')
        )


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    """Admin for QuestionBank with performance tracking"""
    list_display = (
        'id', 'skill', 'difficulty', 'points', 'question_preview',
        'usage_stats', 'success_rate_display', 'created_by_ai', 'created_at'
    )
    list_filter = (
        'difficulty', 'created_by_ai', 'skill__category', 'skill', 'points', 'created_at'
    )
    search_fields = ('question_text', 'skill__name', 'explanation')
    readonly_fields = ('times_used', 'times_correct', 'times_incorrect', 'success_rate', 'created_at', 'updated_at')
    actions = ['reset_statistics', 'duplicate_question']
    
    fieldsets = (
        ('Question Details', {
            'fields': ('skill', 'question_text', 'difficulty', 'points')
        }),
        ('Answer Options', {
            'fields': ('options', 'correct_answer', 'explanation'),
            'description': 'Options will be shuffled per user. Correct answer should match exact option text.'
        }),
        ('Metadata', {
            'fields': ('created_by_ai',)
        }),
        ('Performance Statistics', {
            'fields': ('times_used', 'times_correct', 'times_incorrect', 'success_rate'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_preview(self, obj):
        preview = obj.question_text[:100]
        if len(obj.question_text) > 100:
            preview += '...'
        return preview
    question_preview.short_description = 'Question'
    
    def usage_stats(self, obj):
        return format_html(
            'Used: {} | ✓ {} | ✗ {}',
            obj.times_used, obj.times_correct, obj.times_incorrect
        )
    usage_stats.short_description = 'Usage'
    
    def success_rate_display(self, obj):
        rate = obj.success_rate
        if obj.times_used == 0:
            return format_html('<span style="color: gray;">N/A</span>')
        color = 'green' if rate >= 70 else 'orange' if rate >= 50 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, f'{rate:.1f}%'
        )
    success_rate_display.short_description = 'Success Rate'
    
    def reset_statistics(self, request, queryset):
        queryset.update(times_used=0, times_correct=0, times_incorrect=0)
        self.message_user(request, f'{queryset.count()} question(s) statistics reset.')
    reset_statistics.short_description = 'Reset statistics'
    
    def duplicate_question(self, request, queryset):
        for question in queryset:
            question.pk = None
            question.id = None
            question.times_used = 0
            question.times_correct = 0
            question.times_incorrect = 0
            question.save()
        self.message_user(request, f'{queryset.count()} question(s) duplicated.')
    duplicate_question.short_description = 'Duplicate selected questions'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('skill', 'skill__category')


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    """Admin for AssessmentAttempt with detailed tracking"""
    list_display = (
        'id', 'user', 'skill_name', 'status', 'score_display',
        'percentage_display', 'passed_display', 'time_spent_display',
        'started_at', 'completed_at'
    )
    list_filter = (
        'status', 'passed', 'skill', 'started_at', 'completed_at'
    )
    search_fields = ('user__username', 'user__email', 'skill__name')
    readonly_fields = (
        'user', 'skill', 'assessment', 'question_ids', 'shuffled_options',
        'score', 'max_score', 'percentage', 'proficiency_level',
        'passed', 'started_at', 'completed_at', 'time_spent_seconds',
        'attempt_summary'
    )
    inlines = [UserAnswerInline]
    date_hierarchy = 'started_at'
    actions = ['recalculate_scores', 'mark_as_completed']
    
    fieldsets = (
        ('User & Skill', {
            'fields': ('user', 'skill', 'assessment')
        }),
        ('Assessment Details', {
            'fields': ('question_ids', 'shuffled_options', 'shuffle_seed')
        }),
        ('Results', {
            'fields': ('status', 'score', 'max_score', 'percentage', 'proficiency_level', 'passed')
        }),
        ('Summary', {
            'fields': ('attempt_summary',)
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'time_spent_seconds')
        }),
    )
    
    def skill_name(self, obj):
        return obj.skill.name if obj.skill else (obj.assessment.skill.name if obj.assessment else 'N/A')
    skill_name.short_description = 'Skill'
    skill_name.admin_order_field = 'skill__name'
    
    def score_display(self, obj):
        if obj.score is None or obj.max_score is None:
            return format_html('<span style="color: gray;">N/A</span>')
        return f'{obj.score:.1f}/{obj.max_score:.1f}'
    score_display.short_description = 'Score'
    score_display.admin_order_field = 'score'
    
    def percentage_display(self, obj):
        if obj.percentage is None:
            return format_html('<span style="color: gray;">N/A</span>')
        color = 'green' if obj.percentage >= 70 else 'orange' if obj.percentage >= 60 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, f'{obj.percentage:.1f}%'
        )
    percentage_display.short_description = 'Percentage'
    percentage_display.admin_order_field = 'percentage'
    
    def passed_display(self, obj):
        if obj.passed:
            return format_html('<span style="color: green;">✓ Passed</span>')
        return format_html('<span style="color: red;">✗ Failed</span>')
    passed_display.short_description = 'Status'
    passed_display.admin_order_field = 'passed'
    
    def time_spent_display(self, obj):
        if obj.time_spent_seconds is None:
            return format_html('<span style="color: gray;">N/A</span>')
        minutes = obj.time_spent_seconds // 60
        seconds = obj.time_spent_seconds % 60
        return f'{minutes}m {seconds}s'
    time_spent_display.short_description = 'Time'
    time_spent_display.admin_order_field = 'time_spent_seconds'
    
    def attempt_summary(self, obj):
        """Display detailed attempt summary"""
        answers = obj.user_answers.all()
        if not answers:
            return format_html('<span style="color: orange;">No answers recorded</span>')
        
        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        incorrect = total - correct
        
        total_time = obj.time_spent_seconds if obj.time_spent_seconds is not None else 0
        avg_time = total_time / total if total > 0 else 0
        
        accuracy = (correct/total*100) if total > 0 else 0
        return format_html(
            '<strong>Questions:</strong> {}<br>'
            '<strong>Correct:</strong> <span style="color: green;">{}</span> | '
            '<strong>Incorrect:</strong> <span style="color: red;">{}</span><br>'
            '<strong>Accuracy:</strong> {}<br>'
            '<strong>Total Time:</strong> {}m {}s<br>'
            '<strong>Avg Time/Question:</strong> {}',
            total, correct, incorrect,
            f'{accuracy:.1f}%',
            total_time // 60, total_time % 60,
            f'{avg_time:.1f}s'
        )
    attempt_summary.short_description = 'Attempt Summary'
    
    def recalculate_scores(self, request, queryset):
        for attempt in queryset:
            answers = attempt.user_answers.all()
            attempt.score = sum(a.points_earned for a in answers)
            attempt.calculate_percentage()
            attempt.save()
        self.message_user(request, f'{queryset.count()} attempt(s) recalculated.')
    recalculate_scores.short_description = 'Recalculate scores'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status='in_progress').update(
            status='completed',
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} attempt(s) marked as completed.')
    mark_as_completed.short_description = 'Mark as completed'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'skill', 'assessment')


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    """Admin for UserAnswer with detailed tracking"""
    list_display = (
        'id', 'user_display', 'attempt', 'question_preview',
        'answer_preview', 'is_correct', 'points_earned',
        'time_taken_seconds', 'answered_at'
    )
    list_filter = (
        'is_correct', 'requires_manual_review', 'answered_at',
        'attempt__skill'
    )
    search_fields = (
        'attempt__user__username', 'selected_answer',
        'question_bank__question_text'
    )
    readonly_fields = (
        'attempt', 'question_bank', 'question', 'selected_answer',
        'is_correct', 'points_earned', 'time_taken_seconds',
        'answered_at', 'answer_details'
    )
    date_hierarchy = 'answered_at'
    
    fieldsets = (
        ('Attempt Information', {
            'fields': ('attempt', 'question_bank', 'question')
        }),
        ('User Answer', {
            'fields': ('selected_answer', 'user_answer')
        }),
        ('Evaluation', {
            'fields': ('is_correct', 'points_earned', 'time_taken_seconds')
        }),
        ('Details', {
            'fields': ('answer_details',)
        }),
        ('AI Evaluation', {
            'fields': ('ai_evaluation', 'requires_manual_review'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('answered_at',),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        return obj.attempt.user.username
    user_display.short_description = 'User'
    user_display.admin_order_field = 'attempt__user__username'
    
    def question_preview(self, obj):
        if obj.question_bank:
            text = obj.question_bank.question_text[:60]
            return text + '...' if len(obj.question_bank.question_text) > 60 else text
        return 'N/A'
    question_preview.short_description = 'Question'
    
    def answer_preview(self, obj):
        answer = obj.selected_answer[:50]
        color = 'green' if obj.is_correct else 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, answer
        )
    answer_preview.short_description = 'Answer'
    
    def answer_details(self, obj):
        """Display detailed answer information"""
        if not obj.question_bank:
            return 'No question bank data'
        
        correct_answer = obj.question_bank.correct_answer
        user_answer = obj.selected_answer
        
        return format_html(
            '<strong>User Selected:</strong><br>'
            '<div style="padding: 10px; background: {}; border-radius: 5px; margin: 5px 0;">{}</div>'
            '<strong>Correct Answer:</strong><br>'
            '<div style="padding: 10px; background: #e8f5e9; border-radius: 5px; margin: 5px 0;">{}</div>'
            '<strong>Result:</strong> {}<br>'
            '<strong>Points:</strong> {} / {}<br>'
            '<strong>Time Taken:</strong> {}s',
            '#ffebee' if not obj.is_correct else '#e8f5e9',
            user_answer,
            correct_answer,
            '<span style="color: green;">✓ Correct</span>' if obj.is_correct else '<span style="color: red;">✗ Incorrect</span>',
            f'{obj.points_earned:.1f}',
            obj.question_bank.points,
            obj.time_taken_seconds
        )
    answer_details.short_description = 'Answer Details'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'attempt', 'attempt__user', 'question_bank', 'question'
        )


@admin.register(UserSkillScore)
class UserSkillScoreAdmin(admin.ModelAdmin):
    """Admin for UserSkillScore with proficiency tracking"""
    list_display = (
        'user', 'skill', 'status', 'self_rated_level',
        'verified_level_display', 'proficiency_display',
        'best_score_percentage', 'total_attempts',
        'last_assessment_date'
    )
    list_filter = (
        'status', 'skill__category', 'skill', 'verified_level',
        'last_assessment_date', 'created_at'
    )
    search_fields = ('user__username', 'user__email', 'skill__name')
    readonly_fields = (
        'user', 'skill', 'last_assessment_attempt', 'last_assessment_date',
        'total_attempts', 'best_score_percentage', 'created_at', 'updated_at',
        'proficiency_details'
    )
    actions = ['verify_skills', 'reset_to_claimed']
    date_hierarchy = 'last_assessment_date'
    
    fieldsets = (
        ('User & Skill', {
            'fields': ('user', 'skill')
        }),
        ('Proficiency Levels', {
            'fields': ('self_rated_level', 'verified_level', 'status')
        }),
        ('Assessment History', {
            'fields': ('last_assessment_attempt', 'last_assessment_date', 'total_attempts', 'best_score_percentage')
        }),
        ('Details', {
            'fields': ('proficiency_details',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def verified_level_display(self, obj):
        level = obj.verified_level
        color = 'green' if level >= 7 else 'orange' if level >= 5 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, f'{level:.1f}/10'
        )
    verified_level_display.short_description = 'Verified Level'
    verified_level_display.admin_order_field = 'verified_level'
    
    def proficiency_display(self, obj):
        proficiency = obj.get_proficiency_display()
        colors = {
            'Expert': 'green',
            'Advanced': 'blue',
            'Intermediate': 'orange',
            'Basic': 'goldenrod',
            'Beginner': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(proficiency, 'black'), proficiency
        )
    proficiency_display.short_description = 'Proficiency'
    
    def proficiency_details(self, obj):
        """Display detailed proficiency information"""
        proficiency = obj.get_proficiency_display()
        gap_info = ''
        
        # Show if there's a gap between self-rated and verified
        if obj.self_rated_level > obj.verified_level:
            gap = obj.self_rated_level - obj.verified_level
            gap_info = format_html(
                '<br><strong style="color: orange;">Gap:</strong> Self-rated {} points higher than verified',
                f'{gap:.1f}'
            )
        elif obj.verified_level > obj.self_rated_level:
            gap = obj.verified_level - obj.self_rated_level
            gap_info = format_html(
                '<br><strong style="color: green;">Improvement:</strong> Verified {} points higher than self-rated',
                f'{gap:.1f}'
            )
        
        return format_html(
            '<strong>Proficiency:</strong> {}<br>'
            '<strong>Self-Rated:</strong> {}<br>'
            '<strong>Verified:</strong> {}<br>'
            '<strong>Best Score:</strong> {}<br>'
            '<strong>Total Attempts:</strong> {}<br>'
            '<strong>Status:</strong> {}{}',
            proficiency,
            f'{obj.self_rated_level:.1f}/10',
            f'{obj.verified_level:.1f}/10',
            f'{obj.best_score_percentage:.1f}%',
            obj.total_attempts,
            obj.get_status_display(),
            gap_info
        )
    proficiency_details.short_description = 'Proficiency Details'
    
    def verify_skills(self, request, queryset):
        updated = queryset.filter(verified_level__gte=6).update(status='verified')
        self.message_user(request, f'{updated} skill(s) marked as verified.')
    verify_skills.short_description = 'Mark as verified (if level >= 6)'
    
    def reset_to_claimed(self, request, queryset):
        updated = queryset.update(status='claimed')
        self.message_user(request, f'{updated} skill(s) reset to claimed status.')
    reset_to_claimed.short_description = 'Reset to claimed status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'skill', 'last_assessment_attempt')


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """Admin for Assessment (legacy model)"""
    list_display = ('title', 'skill', 'difficulty_level', 'duration_minutes', 'passing_score_percentage', 'is_active', 'created_at')
    list_filter = ('difficulty_level', 'is_active', 'skill__category', 'created_at')
    search_fields = ('title', 'description', 'skill__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'skill', 'description')
        }),
        ('Settings', {
            'fields': ('difficulty_level', 'duration_minutes', 'passing_score_percentage', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin for Question (legacy model)"""
    list_display = ('id', 'assessment', 'difficulty', 'points', 'order', 'question_preview')
    list_filter = ('difficulty', 'assessment__skill', 'created_at')
    search_fields = ('question_text', 'assessment__title')
    readonly_fields = ('created_at', 'updated_at')
    
    def question_preview(self, obj):
        return obj.question_text[:80] + '...' if len(obj.question_text) > 80 else obj.question_text
    question_preview.short_description = 'Question'


# Register UserSkillProfile proxy model
admin.site.register(UserSkillProfile, UserSkillScoreAdmin)


# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

admin.site.site_header = "Job Elevate - Assessments Admin"
admin.site.site_title = "Assessments Admin"
admin.site.index_title = "Assessment Management Dashboard"
