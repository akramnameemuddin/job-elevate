from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Post, Comment, Like, Follow, Tag, Notification, UserActivity, Event, EventRegistration

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'posts_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['posts_count']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            posts_count=Count('posts')
        )
    
    def posts_count(self, obj):
        return obj.posts_count
    posts_count.short_description = 'Posts Count'
    posts_count.admin_order_field = 'posts_count'

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'post_type', 'likes_count', 'comments_count', 
                   'views', 'is_pinned', 'is_featured', 'is_active', 'created_at']
    list_filter = ['post_type', 'is_pinned', 'is_featured', 'is_active', 'created_at', 'tags']
    search_fields = ['title', 'content', 'author__username', 'author__full_name']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['id', 'slug', 'views', 'likes_count', 'comments_count', 'created_at', 'updated_at']
    filter_horizontal = ['tags']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'slug', 'author', 'post_type', 'content')
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Tags', {
            'fields': ('tags',)
        }),
        ('Settings', {
            'fields': ('is_pinned', 'is_featured', 'is_active')
        }),
        ('Statistics', {
            'fields': ('views', 'likes_count', 'comments_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author').prefetch_related('tags')
    
    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = 'Likes'
    
    def comments_count(self, obj):
        return obj.comments.filter(is_active=True).count()
    comments_count.short_description = 'Comments'
    
    actions = ['make_featured', 'remove_featured', 'make_pinned', 'remove_pinned', 'deactivate_posts']
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} posts marked as featured.')
    make_featured.short_description = "Mark selected posts as featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} posts removed from featured.')
    remove_featured.short_description = "Remove selected posts from featured"
    
    def make_pinned(self, request, queryset):
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'{updated} posts pinned.')
    make_pinned.short_description = "Pin selected posts"
    
    def remove_pinned(self, request, queryset):
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'{updated} posts unpinned.')
    remove_pinned.short_description = "Unpin selected posts"
    
    def deactivate_posts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} posts deactivated.')
    deactivate_posts.short_description = "Deactivate selected posts"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post_title', 'author', 'content_preview', 'parent', 'likes_count', 
                   'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['content', 'author__username', 'author__full_name', 'post__title']
    readonly_fields = ['id', 'likes_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'post', 'parent')
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = 'Post'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = 'Likes'
    
    actions = ['deactivate_comments', 'activate_comments']
    
    def deactivate_comments(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} comments deactivated.')
    deactivate_comments.short_description = "Deactivate selected comments"
    
    def activate_comments(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} comments activated.')
    activate_comments.short_description = "Activate selected comments"

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'content_object', 'created_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['user__username', 'user__full_name']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'post', 'comment')
    
    def content_object(self, obj):
        if obj.content_type == 'post' and obj.post:
            return f"Post: {obj.post.title}"
        elif obj.content_type == 'comment' and obj.comment:
            return f"Comment: {obj.comment.content[:50]}..."
        return "Unknown"
    content_object.short_description = 'Content'

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'content_type', 'content_object', 'created_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['follower__username', 'follower__full_name']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('follower', 'post', 'user')
    
    def content_object(self, obj):
        if obj.content_type == 'post' and obj.post:
            return f"Post: {obj.post.title}"
        elif obj.content_type == 'user' and obj.user:
            return f"User: {obj.user.full_name or obj.user.username}"
        return "Unknown"
    content_object.short_description = 'Following'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'message_preview', 
                   'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'sender', 'post', 'comment')
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'content_object', 'target_user', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__username', 'user__full_name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'post', 'comment', 'target_user')
    
    def content_object(self, obj):
        if obj.post:
            return f"Post: {obj.post.title}"
        elif obj.comment:
            return f"Comment: {obj.comment.content[:50]}..."
        elif obj.target_user:
            return f"User: {obj.target_user.full_name or obj.target_user.username}"
        return "None"
    content_object.short_description = 'Related Content'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'start_datetime', 'end_datetime',
                    'is_free', 'price', 'max_attendees', 'registrations_count',
                    'is_featured', 'is_active']
    list_filter = ['event_type', 'is_free', 'is_featured', 'is_active']
    search_fields = ['title', 'description', 'speaker_name']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['registrations_count', 'created_at', 'updated_at']
    date_hierarchy = 'start_datetime'


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'registered_at', 'is_bookmarked', 'attended']
    list_filter = ['is_bookmarked', 'attended', 'registered_at']
    search_fields = ['event__title', 'user__username']
    readonly_fields = ['registered_at']