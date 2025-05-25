from django.contrib.auth import get_user_model
from .models import Notification, UserActivity

User = get_user_model()

def create_notification(recipient, sender, notification_type, message, post=None, comment=None):
    """
    Create a notification for a user
    """
    # Don't create notification if sender and recipient are the same
    if recipient == sender:
        return None
    
    # Check if similar notification already exists (to avoid spam)
    existing = Notification.objects.filter(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        post=post,
        comment=comment,
        is_read=False
    ).first()
    
    if existing:
        # Update the existing notification's timestamp
        existing.save()  # This will update the created_at due to auto_now_add=False
        return existing
    
    # Create new notification
    notification = Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        post=post,
        comment=comment,
        message=message
    )
    
    return notification

def create_activity(user, activity_type, post=None, comment=None, target_user=None):
    """
    Create a user activity record
    """
    activity = UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        post=post,
        comment=comment,
        target_user=target_user
    )
    
    return activity

def get_user_stats(user):
    """
    Get comprehensive stats for a user
    """
    from django.db.models import Count, Sum
    from .models import Post, Comment, Like, Follow
    
    stats = {
        'posts_count': Post.objects.filter(author=user, is_active=True).count(),
        'comments_count': Comment.objects.filter(author=user, is_active=True).count(),
        'likes_received': Like.objects.filter(
            models.Q(post__author=user) | models.Q(comment__author=user)
        ).count(),
        'likes_given': Like.objects.filter(user=user).count(),
        'followers_count': Follow.objects.filter(user=user, content_type='user').count(),
        'following_count': Follow.objects.filter(follower=user, content_type='user').count(),
        'total_views': Post.objects.filter(author=user, is_active=True).aggregate(
            total=Sum('views')
        )['total'] or 0,
    }
    
    return stats

def get_trending_posts(days=7, limit=5):
    """
    Get trending posts based on recent activity
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count, Q
    from .models import Post
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    trending_posts = Post.objects.filter(
        is_active=True,
        created_at__gte=cutoff_date
    ).annotate(
        recent_likes=Count('likes', filter=Q(likes__created_at__gte=cutoff_date)),
        recent_comments=Count('comments', filter=Q(comments__created_at__gte=cutoff_date))
    ).order_by('-recent_likes', '-recent_comments', '-views')[:limit]
    
    return trending_posts

def get_suggested_users(user, limit=5):
    """
    Get suggested users to follow based on common interests
    """
    from django.db.models import Count, Q
    from .models import Follow, Post
    
    if not user.is_authenticated:
        return User.objects.none()
    
    # Users that current user's connections follow
    following_users = Follow.objects.filter(
        follower=user,
        content_type='user'
    ).values_list('user', flat=True)
    
    # Get users followed by people the current user follows
    suggested_users = User.objects.filter(
        followers__follower__in=following_users
    ).exclude(
        id=user.id
    ).exclude(
        id__in=following_users
    ).annotate(
        mutual_connections=Count('followers__follower', filter=Q(followers__follower__in=following_users))
    ).order_by('-mutual_connections')[:limit]
    
    # If not enough suggestions, get active users
    if suggested_users.count() < limit:
        active_users = User.objects.exclude(
            id=user.id
        ).exclude(
            id__in=following_users
        ).annotate(
            posts_count=Count('posts', filter=Q(posts__is_active=True))
        ).filter(posts_count__gt=0).order_by('-posts_count')[:limit]
        
        # Combine and remove duplicates
        all_suggestions = list(suggested_users) + list(active_users)
        seen_ids = set()
        unique_suggestions = []
        for u in all_suggestions:
            if u.id not in seen_ids:
                unique_suggestions.append(u)
                seen_ids.add(u.id)
                if len(unique_suggestions) >= limit:
                    break
        
        return unique_suggestions
    
    return list(suggested_users)

def get_popular_tags(limit=10):
    """
    Get popular tags based on post count
    """
    from django.db.models import Count
    from .models import Tag
    
    return Tag.objects.annotate(
        posts_count=Count('posts', filter=models.Q(posts__is_active=True))
    ).filter(posts_count__gt=0).order_by('-posts_count')[:limit]

def search_content(query, user=None):
    """
    Comprehensive search across posts, users, and tags
    """
    from django.db.models import Q
    from .models import Post, Tag
    
    results = {
        'posts': [],
        'users': [],
        'tags': []
    }
    
    if not query or len(query.strip()) < 2:
        return results
    
    query = query.strip()
    
    # Search posts
    posts_q = Q(title__icontains=query) | Q(content__icontains=query)
    results['posts'] = Post.objects.filter(
        posts_q, is_active=True
    ).select_related('author').prefetch_related('tags')[:10]
    
    # Search users
    users_q = Q(full_name__icontains=query) | Q(username__icontains=query)
    results['users'] = User.objects.filter(users_q, is_active=True)[:10]
    
    # Search tags
    tags_q = Q(name__icontains=query) | Q(description__icontains=query)
    results['tags'] = Tag.objects.filter(tags_q).annotate(
        posts_count=Count('posts', filter=Q(posts__is_active=True))
    ).filter(posts_count__gt=0)[:10]
    
    return results