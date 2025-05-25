from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
import uuid

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('community:tag_posts', kwargs={'slug': self.slug})

class Post(models.Model):
    POST_TYPES = [
        ('discussion', 'Discussion'),
        ('question', 'Question'),
        ('announcement', 'Announcement'),
        ('job_sharing', 'Job Sharing'),
        ('resource', 'Resource'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='discussion')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    image = models.ImageField(upload_to='community/posts/', blank=True, null=True)
    
    # Engagement fields
    views = models.PositiveIntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['post_type']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('community:post_detail', kwargs={'slug': self.slug})
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def comments_count(self):
        return self.comments.filter(is_active=True).count()
    
    @property
    def followers_count(self):
        return self.followers.count()
    
    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def is_reply(self):
        return self.parent is not None

class Like(models.Model):
    LIKE_TYPES = [
        ('post', 'Post'),
        ('comment', 'Comment'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    content_type = models.CharField(max_length=10, choices=LIKE_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                condition=models.Q(content_type='post'),
                name='unique_post_like'
            ),
            models.UniqueConstraint(
                fields=['user', 'comment'],
                condition=models.Q(content_type='comment'),
                name='unique_comment_like'
            ),
        ]
        indexes = [
            models.Index(fields=['content_type', 'post']),
            models.Index(fields=['content_type', 'comment']),
        ]
    
    def __str__(self):
        if self.content_type == 'post':
            return f'{self.user.username} likes {self.post.title}'
        return f'{self.user.username} likes comment by {self.comment.author.username}'

class Follow(models.Model):
    FOLLOW_TYPES = [
        ('post', 'Post'),
        ('user', 'User'),
    ]
    
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    content_type = models.CharField(max_length=10, choices=FOLLOW_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='followers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'post'],
                condition=models.Q(content_type='post'),
                name='unique_post_follow'
            ),
            models.UniqueConstraint(
                fields=['follower', 'user'],
                condition=models.Q(content_type='user'),
                name='unique_user_follow'
            ),
        ]
    
    def __str__(self):
        if self.content_type == 'post':
            return f'{self.follower.username} follows {self.post.title}'
        return f'{self.follower.username} follows {self.user.username}'

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('like_post', 'Post Liked'),
        ('like_comment', 'Comment Liked'),
        ('comment_post', 'Post Commented'),
        ('reply_comment', 'Comment Replied'),
        ('follow_user', 'User Followed'),
        ('follow_post', 'Post Followed'),
        ('mention', 'Mentioned'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f'Notification for {self.recipient.username}: {self.message}'
    
    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('post_created', 'Created Post'),
        ('post_liked', 'Liked Post'),
        ('comment_created', 'Created Comment'),
        ('comment_liked', 'Liked Comment'),
        ('user_followed', 'Followed User'),
        ('post_followed', 'Followed Post'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='received_activities')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type']),
        ]
    
    def __str__(self):
        return f'{self.user.username} {self.get_activity_type_display()}'