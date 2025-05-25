from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Post, Comment, Like, Follow, Notification, UserActivity
 

User = get_user_model()

@receiver(post_save, sender=Post)
def post_created_handler(sender, instance, created, **kwargs):
    """
    Handle post creation events
    """
    if created:
        # Notify followers of the user about new post
        followers = Follow.objects.filter(
            content_type='user',
            user=instance.author
        ).select_related('follower')
        
        for follow in followers:
            Notification.objects.create(
                recipient=follow.follower,
                sender=instance.author,
                notification_type='post_created',
                post=instance,
                message=f'{instance.author.full_name} created a new post: "{instance.title}"'
            )

@receiver(post_save, sender=Comment)
def comment_created_handler(sender, instance, created, **kwargs):
    """
    Handle comment creation events
    """
    if created:
        # Notify post followers about new comment (except the commenter)
        post_followers = Follow.objects.filter(
            content_type='post',
            post=instance.post
        ).exclude(follower=instance.author).select_related('follower')
        
        for follow in post_followers:
            Notification.objects.create(
                recipient=follow.follower,
                sender=instance.author,
                notification_type='post_activity',
                post=instance.post,
                comment=instance,
                message=f'{instance.author.full_name} commented on a post you\'re following'
            )

@receiver(post_save, sender=Like)
def like_created_handler(sender, instance, created, **kwargs):
    """
    Handle like creation events
    """
    if created:
        # Auto-follow post when user likes it
        if instance.content_type == 'post' and instance.post:
            Follow.objects.get_or_create(
                follower=instance.user,
                content_type='post',
                post=instance.post
            )

@receiver(post_delete, sender=Post)
def post_deleted_handler(sender, instance, **kwargs):
    """
    Clean up related data when post is deleted
    """
    # Delete related notifications
    Notification.objects.filter(post=instance).delete()
    
    # Delete related activities
    UserActivity.objects.filter(post=instance).delete()

@receiver(post_delete, sender=Comment)
def comment_deleted_handler(sender, instance, **kwargs):
    """
    Clean up related data when comment is deleted
    """
    # Delete related notifications
    Notification.objects.filter(comment=instance).delete()
    
    # Delete related activities
    UserActivity.objects.filter(comment=instance).delete()

@receiver(post_delete, sender=User)
def user_deleted_handler(sender, instance, **kwargs):
    """
    Clean up related data when user is deleted
    """
    # Delete related notifications
    Notification.objects.filter(
        models.Q(recipient=instance) | models.Q(sender=instance)
    ).delete()
    
    # Delete related activities
    UserActivity.objects.filter(
        models.Q(user=instance) | models.Q(target_user=instance)
    ).delete()