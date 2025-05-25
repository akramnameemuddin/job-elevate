from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
import json

from .models import Post, Comment, Like, Follow, Tag, Notification, UserActivity
from .forms import PostForm, CommentForm, PostFilterForm
from .utils import create_notification, create_activity

User = get_user_model()

class CommunityHomeView(ListView):
    model = Post
    template_name = 'community/home.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Post.objects.select_related('author').prefetch_related(
            'tags', 'likes', 'comments'
        ).filter(is_active=True)
        
        # Filter by post type
        post_type = self.request.GET.get('type')
        if post_type and post_type != 'all':
            queryset = queryset.filter(post_type=post_type)
        
        # Filter by tag
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(author__full_name__icontains=search_query)
            )
        
        # Sort options
        sort_by = self.request.GET.get('sort', 'recent')
        if sort_by == 'popular':
            queryset = queryset.annotate(
                total_likes=Count('likes'),
                total_comments=Count('comments')
            ).order_by('-total_likes', '-total_comments', '-created_at')
        elif sort_by == 'most_viewed':
            queryset = queryset.order_by('-views', '-created_at')
        else:  # recent
            queryset = queryset.order_by('-is_pinned', '-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = PostFilterForm(self.request.GET)
        context['popular_tags'] = Tag.objects.annotate(
            post_count=Count('posts')
        ).filter(post_count__gt=0).order_by('-post_count')[:10]
        context['current_filter'] = self.request.GET.dict()
        
        # Add user-specific data if logged in
        if self.request.user.is_authenticated:
            context['user_liked_posts'] = set(
                Like.objects.filter(
                    user=self.request.user,
                    content_type='post'
                ).values_list('post_id', flat=True)
            )
            context['user_followed_posts'] = set(
                Follow.objects.filter(
                    follower=self.request.user,
                    content_type='post'
                ).values_list('post_id', flat=True)
            )
        
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'community/post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        obj.increment_views()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        
        # Get comments with replies
        comments = Comment.objects.select_related('author').filter(
            post=post, parent=None, is_active=True
        ).prefetch_related(
            Prefetch('replies', queryset=Comment.objects.select_related('author').filter(is_active=True))
        )
        
        context['comments'] = comments
        context['comment_form'] = CommentForm()
        
        # User-specific data
        if self.request.user.is_authenticated:
            context['user_liked_post'] = Like.objects.filter(
                user=self.request.user, post=post, content_type='post'
            ).exists()
            context['user_following_post'] = Follow.objects.filter(
                follower=self.request.user, post=post, content_type='post'
            ).exists()
            context['user_liked_comments'] = set(
                Like.objects.filter(
                    user=self.request.user,
                    content_type='comment',
                    comment__post=post
                ).values_list('comment_id', flat=True)
            )
        
        # Related posts
        context['related_posts'] = Post.objects.filter(
            tags__in=post.tags.all(),
            is_active=True
        ).exclude(id=post.id).distinct()[:5]
        
        return context

@method_decorator(login_required, name='dispatch')
class PostCreateView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'community/post_create.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        
        # Create activity
        create_activity(
            user=self.request.user,
            activity_type='post_created',
            post=self.object
        )
        
        messages.success(self.request, 'Your post has been created successfully!')
        return response

@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'community/post_edit.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Your post has been updated successfully!')
        return super().form_valid(form)

@login_required
@require_POST
def add_comment(request, slug):
    post = get_object_or_404(Post, slug=slug, is_active=True)
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        
        # Handle reply
        parent_id = request.POST.get('parent_id')
        if parent_id:
            parent_comment = get_object_or_404(Comment, id=parent_id)
            comment.parent = parent_comment
        
        comment.save()
        
        # Create notification for post author (if not self)
        if post.author != request.user:
            create_notification(
                recipient=post.author,
                sender=request.user,
                notification_type='comment_post',
                post=post,
                comment=comment,
                message=f'{request.user.full_name} commented on your post "{post.title}"'
            )
        
        # Create notification for parent comment author (if reply and not self)
        if comment.parent and comment.parent.author != request.user:
            create_notification(
                recipient=comment.parent.author,
                sender=request.user,
                notification_type='reply_comment',
                post=post,
                comment=comment,
                message=f'{request.user.full_name} replied to your comment'
            )
        
        # Create activity
        create_activity(
            user=request.user,
            activity_type='comment_created',
            post=post,
            comment=comment
        )
        
        messages.success(request, 'Your comment has been added!')
    else:
        messages.error(request, 'Please correct the errors in your comment.')
    
    return redirect('community:post_detail', slug=post.slug)

@login_required
@require_POST
def toggle_like(request):
    content_type = request.POST.get('content_type')
    content_id = request.POST.get('content_id')
    
    if content_type == 'post':
        content_obj = get_object_or_404(Post, id=content_id)
        like_obj, created = Like.objects.get_or_create(
            user=request.user,
            content_type='post',
            post=content_obj
        )
        
        if not created:
            like_obj.delete()
            liked = False
        else:
            liked = True
            # Create notification (if not self-like)
            if content_obj.author != request.user:
                create_notification(
                    recipient=content_obj.author,
                    sender=request.user,
                    notification_type='like_post',
                    post=content_obj,
                    message=f'{request.user.full_name} liked your post "{content_obj.title}"'
                )
            
            # Create activity
            create_activity(
                user=request.user,
                activity_type='post_liked',
                post=content_obj
            )
        
        likes_count = content_obj.likes_count
    
    elif content_type == 'comment':
        content_obj = get_object_or_404(Comment, id=content_id)
        like_obj, created = Like.objects.get_or_create(
            user=request.user,
            content_type='comment',
            comment=content_obj
        )
        
        if not created:
            like_obj.delete()
            liked = False
        else:
            liked = True
            # Create notification (if not self-like)
            if content_obj.author != request.user:
                create_notification(
                    recipient=content_obj.author,
                    sender=request.user,
                    notification_type='like_comment',
                    post=content_obj.post,
                    comment=content_obj,
                    message=f'{request.user.full_name} liked your comment'
                )
            
            # Create activity
            create_activity(
                user=request.user,
                activity_type='comment_liked',
                comment=content_obj
            )
        
        likes_count = content_obj.likes_count
    
    else:
        return JsonResponse({'error': 'Invalid content type'}, status=400)
    
    return JsonResponse({
        'liked': liked,
        'likes_count': likes_count
    })

@login_required
@require_POST
def toggle_follow(request):
    content_type = request.POST.get('content_type')
    content_id = request.POST.get('content_id')
    
    if content_type == 'post':
        content_obj = get_object_or_404(Post, id=content_id)
        follow_obj, created = Follow.objects.get_or_create(
            follower=request.user,
            content_type='post',
            post=content_obj
        )
        
        if not created:
            follow_obj.delete()
            following = False
        else:
            following = True
            # Create activity
            create_activity(
                user=request.user,
                activity_type='post_followed',
                post=content_obj
            )
        
        followers_count = content_obj.followers_count
    
    elif content_type == 'user':
        content_obj = get_object_or_404(User, id=content_id)
        if content_obj == request.user:
            return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
        
        follow_obj, created = Follow.objects.get_or_create(
            follower=request.user,
            content_type='user',
            user=content_obj
        )
        
        if not created:
            follow_obj.delete()
            following = False
        else:
            following = True
            # Create notification
            create_notification(
                recipient=content_obj,
                sender=request.user,
                notification_type='follow_user',
                message=f'{request.user.full_name} started following you'
            )
            
            # Create activity
            create_activity(
                user=request.user,
                activity_type='user_followed',
                target_user=content_obj
            )
        
        followers_count = content_obj.followers.count()
    
    else:
        return JsonResponse({'error': 'Invalid content type'}, status=400)
    
    return JsonResponse({
        'following': following,
        'followers_count': followers_count
    })

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'post', 'comment').order_by('-created_at')
    
    # Mark all as read when viewed
    notifications.filter(is_read=False).update(is_read=True)
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'community/notifications.html', {
        'notifications': page_obj
    })

@login_required
def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    
    # Get user's posts
    posts = Post.objects.filter(
        author=profile_user, is_active=True
    ).select_related('author').prefetch_related('tags', 'likes', 'comments')
    
    # Get user's activities
    activities = UserActivity.objects.filter(
        user=profile_user
    ).select_related('post', 'comment', 'target_user').order_by('-created_at')[:10]
    
    # Check if current user follows this user
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user,
            content_type='user',
            user=profile_user
        ).exists()
    
    context = {
        'profile_user': profile_user,
        'posts': posts,
        'activities': activities,
        'is_following': is_following,
        'followers_count': profile_user.followers.count(),
        'following_count': profile_user.following.count(),
        'posts_count': posts.count(),
    }
    
    return render(request, 'community/user_profile.html', context)

class TagPostsView(ListView):
    model = Post
    template_name = 'community/tag_posts.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return Post.objects.filter(
            tags=self.tag, is_active=True
        ).select_related('author').prefetch_related('tags', 'likes', 'comments')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        return context

@login_required
def my_posts(request):
    posts = Post.objects.filter(
        author=request.user
    ).select_related('author').prefetch_related('tags', 'likes', 'comments')
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'community/my_posts.html', {
        'posts': page_obj
    })

@login_required
@require_POST
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user)
    post.delete()
    messages.success(request, 'Post deleted successfully!')
    return redirect('community:my_posts')

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    post_slug = comment.post.slug
    comment.delete()
    messages.success(request, 'Comment deleted successfully!')
    return redirect('community:post_detail', slug=post_slug)