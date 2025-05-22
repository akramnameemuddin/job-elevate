from django.contrib import admin
from .models import JobView, JobBookmark, UserJobPreference, JobRecommendation, UserSimilarity

@admin.register(JobView)
class JobViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'view_count', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('user__username', 'user__email', 'job__title')
    date_hierarchy = 'viewed_at'

@admin.register(JobBookmark)
class JobBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'bookmarked_at')
    list_filter = ('bookmarked_at',)
    search_fields = ('user__username', 'user__email', 'job__title')
    date_hierarchy = 'bookmarked_at'

@admin.register(UserJobPreference)
class UserJobPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'remote_preference', 'min_salary_expectation', 'updated_at')
    list_filter = ('remote_preference', 'updated_at')
    search_fields = ('user__username', 'user__email')
    date_hierarchy = 'updated_at'

@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'score', 'reason', 'is_viewed', 'created_at')
    list_filter = ('is_viewed', 'created_at')
    search_fields = ('user__username', 'user__email', 'job__title', 'reason')
    date_hierarchy = 'created_at'

@admin.register(UserSimilarity)
class UserSimilarityAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'similarity_score', 'last_calculated')
    list_filter = ('last_calculated',)
    search_fields = ('user1__username', 'user1__email', 'user2__username', 'user2__email')
    date_hierarchy = 'last_calculated'