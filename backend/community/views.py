from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
import json

from .models import Post, Comment, Like, Follow, Tag, Notification, UserActivity, Event, EventRegistration
from .forms import PostForm, CommentForm, PostFilterForm
from .utils import create_notification, create_activity, get_user_stats, get_trending_posts, get_suggested_users, get_popular_tags

User = get_user_model()

@method_decorator(login_required, name='dispatch')
class CommunityView(View):
    """Single view to handle all community functionality"""
    template_name = 'community/community.html'
    
    def get(self, request, *args, **kwargs):
        section = request.GET.get('section', 'home')
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self._handle_ajax_request(request, section)
        
        # Base context
        context = self._get_base_context(request)
        context['section'] = section
        
        # Load section-specific context
        try:
            if section == 'home':
                context.update(self._get_home_context(request))
            elif section == 'my-posts':
                context.update(self._get_my_posts_context(request))
            elif section == 'notifications':
                context.update(self._get_notifications_context(request))
            elif section == 'post-detail':
                context.update(self._get_post_detail_context(request))
            elif section == 'user-profile':
                context.update(self._get_user_profile_context(request))
            elif section == 'tag-posts':
                context.update(self._get_tag_posts_context(request))
            elif section == 'create-post':
                context.update(self._get_create_post_context(request))
            elif section == 'edit-post':
                context.update(self._get_edit_post_context(request))
            else:
                section = 'home'
                context['section'] = 'home'
                context.update(self._get_home_context(request))
        except Exception as e:
            messages.error(request, f'Error loading section: {str(e)}')
            context['section'] = 'home'
            context.update(self._get_home_context(request))
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        section = request.GET.get('section', 'home')
        
        try:
            if section == 'create-post':
                return self._handle_create_post(request)
            elif section == 'edit-post':
                return self._handle_edit_post(request)
            elif section == 'add-comment':
                return self._handle_add_comment(request)
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=500)
            messages.error(request, f'Error: {str(e)}')
        
        return self.get(request, *args, **kwargs)
    
    def _get_base_context(self, request):
        """Get base context available to all sections"""
        try:
            unread_count = 0
            popular_tags = []
            suggested_users = []
            trending_posts = []
            
            if request.user.is_authenticated:
                unread_count = Notification.objects.filter(
                    recipient=request.user, is_read=False
                ).count()
                
                popular_tags = get_popular_tags(limit=10)
                suggested_users = get_suggested_users(request.user, limit=5)
                trending_posts = get_trending_posts(limit=5)
            
            return {
                'user': request.user,
                'popular_tags': popular_tags,
                'suggested_users': suggested_users,
                'trending_posts': trending_posts,
                'unread_notifications_count': unread_count,
            }
        except Exception as e:
            print(f"Error in base context: {e}")
            return {
                'user': request.user,
                'popular_tags': [],
                'suggested_users': [],
                'trending_posts': [],
                'unread_notifications_count': 0,
            }
    
    def _handle_ajax_request(self, request, section):
        """Handle AJAX requests for dynamic content loading"""
        try:
            if section == 'my-posts':
                posts = self._get_user_posts(request.user)
                html = render_to_string('community/partials/posts_list.html', {
                    'posts': posts, 
                    'request': request,
                    'user_liked_posts': self._get_user_liked_posts(request.user, posts),
                    'user_followed_posts': self._get_user_followed_posts(request.user, posts),
                }, request=request)
                return JsonResponse({'html': html, 'success': True})
                
            elif section == 'notifications':
                notifications = self._get_user_notifications(request.user)
                html = render_to_string('community/partials/notifications_list.html', {
                    'notifications': notifications,
                    'request': request
                }, request=request)
                return JsonResponse({'html': html, 'success': True})
                
            elif section == 'post-detail':
                slug = request.GET.get('slug')
                if not slug:
                    return JsonResponse({'error': 'Post slug required'}, status=400)
                
                try:
                    post = Post.objects.select_related('author').prefetch_related('tags').get(
                        slug=slug, is_active=True
                    )
                    post.increment_views()
                    
                    context = self._get_post_detail_data(request, post)
                    html = render_to_string('community/partials/post_detail.html', context, request=request)
                    return JsonResponse({'html': html, 'success': True})
                except Post.DoesNotExist:
                    return JsonResponse({'error': 'Post not found'}, status=404)
            
            elif section == 'edit-post':
                slug = request.GET.get('slug')
                if not slug:
                    return JsonResponse({'error': 'Post slug required'}, status=400)
                
                try:
                    post = Post.objects.get(slug=slug, author=request.user, is_active=True)
                    # Return post data for form population
                    post_data = {
                        'id': str(post.id),
                        'title': post.title,
                        'content': post.content,
                        'post_type': post.post_type,
                        'tags': list(post.tags.values_list('id', flat=True)),
                        'image_url': post.image.url if post.image else None,
                    }
                    return JsonResponse({'success': True, 'post': post_data})
                except Post.DoesNotExist:
                    return JsonResponse({'error': 'Post not found or permission denied'}, status=404)
            
            return JsonResponse({'error': 'Invalid section'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def _get_home_context(self, request):
        """Get context for home/feed section"""
        try:
            queryset = Post.objects.select_related('author').prefetch_related('tags').filter(is_active=True)
            
            # Apply filters
            post_type = request.GET.get('type')
            if post_type and post_type != 'all':
                queryset = queryset.filter(post_type=post_type)
            
            tag_slug = request.GET.get('tag')
            if tag_slug:
                try:
                    tag = Tag.objects.get(slug=tag_slug)
                    queryset = queryset.filter(tags=tag)
                except Tag.DoesNotExist:
                    pass
            
            search_query = request.GET.get('search')
            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(content__icontains=search_query) |
                    Q(author__full_name__icontains=search_query) |
                    Q(author__username__icontains=search_query)
                ).distinct()
            
            # Sort options
            sort_by = request.GET.get('sort', 'recent')
            if sort_by == 'popular':
                queryset = queryset.annotate(
                    total_likes=Count('likes'),
                    total_comments=Count('comments')
                ).order_by('-total_likes', '-total_comments', '-created_at')
            elif sort_by == 'most_viewed':
                queryset = queryset.order_by('-views', '-created_at')
            else:
                queryset = queryset.order_by('-is_pinned', '-created_at')
            
            # Pagination
            paginator = Paginator(queryset, 10)
            page_number = request.GET.get('page', 1)
            posts = paginator.get_page(page_number)
            
            # User interaction data
            user_liked_posts = self._get_user_liked_posts(request.user, posts)
            user_followed_posts = self._get_user_followed_posts(request.user, posts)
            
            return {
                'posts': posts,
                'filter_form': PostFilterForm(request.GET),
                'current_filter': request.GET.dict(),
                'user_liked_posts': user_liked_posts,
                'user_followed_posts': user_followed_posts,
            }
        except Exception as e:
            return {'error': f'Error loading posts: {str(e)}', 'posts': []}
    
    def _get_user_liked_posts(self, user, posts):
        """Get set of post IDs that user has liked"""
        if not user.is_authenticated:
            return set()
        
        post_ids = [post.id for post in posts] if hasattr(posts, '__iter__') else []
        return set(
            Like.objects.filter(
                user=user,
                content_type='post',
                post_id__in=post_ids
            ).values_list('post_id', flat=True)
        )
    
    def _get_user_followed_posts(self, user, posts):
        """Get set of post IDs that user is following"""
        if not user.is_authenticated:
            return set()
        
        post_ids = [post.id for post in posts] if hasattr(posts, '__iter__') else []
        return set(
            Follow.objects.filter(
                follower=user,
                content_type='post',
                post_id__in=post_ids
            ).values_list('post_id', flat=True)
        )
    
    def _get_user_posts(self, user):
        """Get user's posts with pagination"""
        posts = Post.objects.filter(
            author=user, is_active=True
        ).select_related('author').prefetch_related('tags').order_by('-created_at')
        
        paginator = Paginator(posts, 10)
        page_number = 1  # For AJAX, we'll start with page 1
        return paginator.get_page(page_number)
    
    def _get_user_notifications(self, user):
        """Get user's notifications with pagination"""
        notifications = Notification.objects.filter(
            recipient=user
        ).select_related('sender', 'post', 'comment').order_by('-created_at')
        
        # Mark as read when accessed
        notifications.filter(is_read=False).update(is_read=True)
        
        paginator = Paginator(notifications, 20)
        page_number = 1  # For AJAX, we'll start with page 1
        return paginator.get_page(page_number)
    
    def _get_post_detail_context(self, request):
        """Get context for post-detail section loaded via full page (non-AJAX)"""
        slug = request.GET.get('slug')
        if not slug:
            raise Http404('Post slug is required')
        post = get_object_or_404(Post, slug=slug, is_active=True)
        post.increment_views()
        return self._get_post_detail_data(request, post)

    def _get_post_detail_data(self, request, post):
        """Get post detail context data"""
        comments = Comment.objects.select_related('author').filter(
            post=post, parent=None, is_active=True
        ).prefetch_related(
            Prefetch('replies', queryset=Comment.objects.select_related('author').filter(is_active=True))
        ).order_by('created_at')
        
        # User interaction data
        user_liked_post = False
        user_following_post = False
        user_liked_comments = set()
        
        if request.user.is_authenticated:
            user_liked_post = Like.objects.filter(
                user=request.user, post=post, content_type='post'
            ).exists()
            user_following_post = Follow.objects.filter(
                follower=request.user, post=post, content_type='post'
            ).exists()
            user_liked_comments = set(
                Like.objects.filter(
                    user=request.user,
                    content_type='comment',
                    comment__post=post
                ).values_list('comment_id', flat=True)
            )
        
        # Related posts
        related_posts = Post.objects.filter(
            tags__in=post.tags.all(),
            is_active=True
        ).exclude(id=post.id).distinct()[:5]
        
        return {
            'current_post': post,
            'comments': comments,
            'comment_form': CommentForm(),
            'user_liked_post': user_liked_post,
            'user_following_post': user_following_post,
            'user_liked_comments': user_liked_comments,
            'related_posts': related_posts,
        }
    
    def _get_my_posts_context(self, request):
        """Get context for user's posts section"""
        try:
            posts = Post.objects.filter(
                author=request.user,
                is_active=True
            ).select_related('author').prefetch_related('tags', 'likes', 'comments').order_by('-created_at')
            
            # Get user interaction data for my posts
            user_liked_posts = set()
            user_followed_posts = set()
            if posts.exists():
                user_liked_posts = set(
                    Like.objects.filter(
                        user=request.user,
                        content_type='post',
                        post__in=posts
                    ).values_list('post_id', flat=True)
                )
                user_followed_posts = set(
                    Follow.objects.filter(
                        follower=request.user,
                        content_type='post',
                        post__in=posts
                    ).values_list('post_id', flat=True)
                )
            
            paginator = Paginator(posts, 10)
            page_number = request.GET.get('page', 1)
            posts_page = paginator.get_page(page_number)
            
            return {
                'my_posts': posts_page,
                'user_stats': get_user_stats(request.user),
                'user_liked_posts': user_liked_posts,
                'user_followed_posts': user_followed_posts,
            }
        except Exception as e:
            return {'error': f'Error loading posts: {str(e)}', 'my_posts': []}
    
    def _get_notifications_context(self, request):
        """Get context for notifications section"""
        try:
            notifications = Notification.objects.filter(
                recipient=request.user
            ).select_related('sender', 'post', 'comment').order_by('-created_at')
            
            # Mark all as read when viewed
            unread_notifications = notifications.filter(is_read=False)
            unread_notifications.update(is_read=True)
            
            paginator = Paginator(notifications, 20)
            page_number = request.GET.get('page', 1)
            notifications_page = paginator.get_page(page_number)
            
            return {
                'notifications': notifications_page,
            }
        except Exception as e:
            return {'error': f'Error loading notifications: {str(e)}', 'notifications': []}
    
    def _get_user_profile_context(self, request):
        """Get context for user profile section"""
        username = request.GET.get('username')
        if not username:
            return {'error': 'User not found'}
        
        try:
            profile_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return {'error': 'User not found'}
        
        try:
            # Get user's posts
            posts = Post.objects.filter(
                author=profile_user, is_active=True
            ).select_related('author').prefetch_related('tags', 'likes', 'comments').order_by('-created_at')
            
            # Get user's activities
            activities = UserActivity.objects.filter(
                user=profile_user
            ).select_related('post', 'comment', 'target_user').order_by('-created_at')[:10]
            
            # Check if current user follows this user
            is_following = False
            if request.user != profile_user and request.user.is_authenticated:
                is_following = Follow.objects.filter(
                    follower=request.user,
                    content_type='user',
                    user=profile_user
                ).exists()
            
            return {
                'profile_user': profile_user,
                'profile_posts': posts,
                'profile_activities': activities,
                'is_following': is_following,
                'profile_stats': get_user_stats(profile_user),
            }
        except Exception as e:
            return {'error': f'Error loading profile: {str(e)}'}
    
    def _get_tag_posts_context(self, request):
        """Get context for tag-based posts section"""
        tag_slug = request.GET.get('tag')
        if not tag_slug:
            return {'error': 'Tag not found'}
        
        try:
            tag = Tag.objects.get(slug=tag_slug)
        except Tag.DoesNotExist:
            return {'error': 'Tag not found'}
        
        try:
            posts = Post.objects.filter(
                tags=tag, is_active=True
            ).select_related('author').prefetch_related('tags', 'likes', 'comments').order_by('-created_at')
            
            paginator = Paginator(posts, 10)
            page_number = request.GET.get('page', 1)
            posts_page = paginator.get_page(page_number)
            
            return {
                'current_tag': tag,
                'tag_posts': posts_page,
            }
        except Exception as e:
            return {'error': f'Error loading tag posts: {str(e)}'}
    
    def _get_create_post_context(self, request):
        """Get context for create post section"""
        return {
            'post_form': PostForm(),
        }
    
    def _get_edit_post_context(self, request):
        """Get context for edit post section"""
        slug = request.GET.get('slug')
        if not slug:
            return {'error': 'Post not found'}
        
        try:
            post = Post.objects.get(slug=slug, author=request.user, is_active=True)
            return {
                'edit_post': post,
                'post_form': PostForm(instance=post),
            }
        except Post.DoesNotExist:
            return {'error': 'Post not found or you do not have permission to edit'}

    def _handle_create_post(self, request):
        """Handle post creation"""
        form = PostForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                post = form.save(commit=False)
                post.author = request.user
                post.save()
                form.save_m2m()  # Save tags
                
                # Create activity
                create_activity(
                    user=request.user,
                    activity_type='post_created',
                    post=post
                )
                
                messages.success(request, 'Your post has been created successfully!')
                
                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': f'/community/?section=post-detail&slug={post.slug}'
                    })
                
                return redirect(f'/community/?section=post-detail&slug={post.slug}')
            except Exception as e:
                error_msg = f'Error creating post: {str(e)}'
                messages.error(request, error_msg)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': error_msg}, status=500)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Form validation failed', 'errors': form.errors}, status=400)
        
        # Return to form with errors
        context = self._get_base_context(request)
        context.update({
            'section': 'create-post',
            'post_form': form,
        })
        return render(request, self.template_name, context)
    
    def _handle_edit_post(self, request):
        """Handle post editing"""
        slug = request.GET.get('slug')
        if not slug:
            messages.error(request, 'Post not found')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Post not found'}, status=404)
            return redirect('/community/?section=my-posts')
        
        try:
            post = Post.objects.get(slug=slug, author=request.user, is_active=True)
        except Post.DoesNotExist:
            messages.error(request, 'Post not found or you do not have permission to edit')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Post not found or permission denied'}, status=404)
            return redirect('/community/?section=my-posts')
        
        form = PostForm(request.POST, request.FILES, instance=post)
        
        if form.is_valid():
            try:
                updated_post = form.save()
                messages.success(request, 'Your post has been updated successfully!')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': f'/community/?section=post-detail&slug={updated_post.slug}'
                    })
                
                return redirect(f'/community/?section=post-detail&slug={updated_post.slug}')
            except Exception as e:
                messages.error(request, f'Error updating post: {str(e)}')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': str(e)}, status=500)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Form validation failed', 'errors': form.errors}, status=400)
            messages.error(request, 'Please correct the errors in the form.')
        context = {
            'section': 'edit-post',
            'edit_post': post,
            'post_form': form,
            'popular_tags': get_popular_tags(limit=10),
            'suggested_users': get_suggested_users(request.user, limit=5),
            'unread_notifications_count': Notification.objects.filter(
                recipient=request.user, is_read=False
            ).count(),
        }
        return render(request, self.template_name, context)
    
    def _handle_add_comment(self, request):
        """Handle adding comments"""
        slug = request.GET.get('slug')
        if not slug:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Post not found'}, status=404)
            messages.error(request, 'Post not found')
            return redirect('?section=home')
        
        try:
            post = get_object_or_404(Post, slug=slug, is_active=True)
        except Post.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Post not found'}, status=404)
            messages.error(request, 'Post not found')
            return redirect('?section=home')
        
        form = CommentForm(request.POST)
        
        if form.is_valid():
            try:
                comment = form.save(commit=False)
                comment.post = post
                comment.author = request.user
                
                # Handle reply
                parent_id = request.POST.get('parent_id')
                if parent_id:
                    try:
                        parent_comment = Comment.objects.get(id=parent_id)
                        comment.parent = parent_comment
                    except Comment.DoesNotExist:
                        pass
                
                comment.save()
                
                # Create notifications and activities
                if post.author != request.user:
                    create_notification(
                        recipient=post.author,
                        sender=request.user,
                        notification_type='comment_post',
                        post=post,
                        comment=comment,
                        message=f'{request.user.full_name or request.user.username} commented on your post "{post.title}"'
                    )
                
                if comment.parent and comment.parent.author != request.user:
                    create_notification(
                        recipient=comment.parent.author,
                        sender=request.user,
                        notification_type='reply_comment',
                        post=post,
                        comment=comment,
                        message=f'{request.user.full_name or request.user.username} replied to your comment'
                    )
                
                create_activity(
                    user=request.user,
                    activity_type='comment_created',
                    post=post,
                    comment=comment
                )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Comment added successfully!'})
                
                messages.success(request, 'Your comment has been added!')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': str(e)}, status=500)
                messages.error(request, f'Error adding comment: {str(e)}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Comment validation failed', 'errors': form.errors}, status=400)
            messages.error(request, 'Please correct the errors in your comment.')
        
        return HttpResponseRedirect(f'/community/?section=post-detail&slug={post.slug}')

@login_required
@require_POST
def toggle_like(request):
    """Toggle like status for posts or comments"""
    try:
        content_type = request.POST.get('content_type')
        content_id = request.POST.get('content_id')
        
        if not content_type or not content_id:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        
        if content_type == 'post':
            try:
                content_obj = Post.objects.get(id=content_id, is_active=True)
            except Post.DoesNotExist:
                return JsonResponse({'error': 'Post not found'}, status=404)
            
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
                # Create notification for post author
                if content_obj.author != request.user:
                    create_notification(
                        recipient=content_obj.author,
                        sender=request.user,
                        notification_type='like_post',
                        post=content_obj,
                        message=f'{request.user.full_name or request.user.username} liked your post "{content_obj.title}"'
                    )
                
                # Create activity
                create_activity(
                    user=request.user,
                    activity_type='post_liked',
                    post=content_obj
                )
            
            likes_count = content_obj.likes.count()
        
        elif content_type == 'comment':
            try:
                content_obj = Comment.objects.get(id=content_id, is_active=True)
            except Comment.DoesNotExist:
                return JsonResponse({'error': 'Comment not found'}, status=404)
            
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
                # Create notification for comment author
                if content_obj.author != request.user:
                    create_notification(
                        recipient=content_obj.author,
                        sender=request.user,
                        notification_type='like_comment',
                        post=content_obj.post,
                        comment=content_obj,
                        message=f'{request.user.full_name or request.user.username} liked your comment'
                    )
                
                # Create activity
                create_activity(
                    user=request.user,
                    activity_type='comment_liked',
                    comment=content_obj
                )
            
            likes_count = content_obj.likes.count()
        
        else:
            return JsonResponse({'error': 'Invalid content type'}, status=400)
        
        return JsonResponse({
            'liked': liked,
            'likes_count': likes_count
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
            create_notification(
                recipient=content_obj,
                sender=request.user,
                notification_type='follow_user',
                message=f'{request.user.full_name or request.user.username} started following you'
            )
            
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
@require_POST
def delete_post(request):
    """Delete a post - only by the author"""
    try:
        post_id = request.POST.get('post_id')
        if not post_id:
            return JsonResponse({'error': 'Post ID required'}, status=400)
        
        try:
            post = Post.objects.get(id=post_id, author=request.user, is_active=True)
            post_title = post.title
            post.delete()
            
            messages.success(request, f'Post "{post_title}" deleted successfully!')
            return JsonResponse({'success': True, 'message': f'Post "{post_title}" deleted successfully!'})
        except Post.DoesNotExist:
            return JsonResponse({'error': 'Post not found or you do not have permission to delete it'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def delete_comment(request):
    comment_id = request.POST.get('comment_id')
    if not comment_id:
        return JsonResponse({'error': 'Comment ID required'}, status=400)
    
    try:
        comment = Comment.objects.get(id=comment_id, author=request.user)
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')
        return JsonResponse({'success': True})
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found or permission denied'}, status=404)

@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    try:
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Add helper view functions for direct URL access
@login_required
def post_detail_view(request, slug):
    """Redirect to community view with post detail"""
    return redirect(f'/community/?section=post-detail&slug={slug}')

@login_required
def edit_post_view(request, slug):
    """Redirect to community view with edit post"""
    return redirect(f'/community/?section=edit-post&slug={slug}')

@login_required
def user_profile_view(request, username):
    """Redirect to community view with user profile"""
    return redirect(f'/community/?section=user-profile&username={username}')

@login_required
def tag_posts_view(request, slug):
    """Redirect to community view with tag posts"""
    return redirect(f'/community/?section=tag-posts&tag={slug}')


# ── Events views ──────────────────────────────────────────────

@login_required
def events_view(request):
    """Virtual events listing page (workshops, webinars, career sessions)"""
    now = timezone.now()

    # Filters
    category = request.GET.get('category', 'all')
    search_q = request.GET.get('q', '').strip()
    time_filter = request.GET.get('time', 'upcoming')     # upcoming | past | all

    events_qs = Event.objects.filter(is_active=True).annotate(
        registration_count=Count('registrations')
    ).select_related('created_by')

    if category and category != 'all':
        events_qs = events_qs.filter(event_type=category)
    if search_q:
        events_qs = events_qs.filter(
            Q(title__icontains=search_q) | Q(description__icontains=search_q)
        )
    if time_filter == 'upcoming':
        events_qs = events_qs.filter(start_datetime__gt=now).order_by('start_datetime')
    elif time_filter == 'past':
        events_qs = events_qs.filter(end_datetime__lt=now).order_by('-start_datetime')
    else:
        events_qs = events_qs.order_by('start_datetime')

    paginator = Paginator(events_qs, 9)
    page = request.GET.get('page', 1)
    events = paginator.get_page(page)

    # Featured event (next upcoming featured, or first upcoming)
    featured = Event.objects.filter(
        is_active=True, is_featured=True, start_datetime__gt=now
    ).annotate(registration_count=Count('registrations')).first()
    if not featured:
        featured = Event.objects.filter(
            is_active=True, start_datetime__gt=now
        ).annotate(registration_count=Count('registrations')).first()

    # Stats
    upcoming_count = Event.objects.filter(is_active=True, start_datetime__gt=now).count()
    live_count = Event.objects.filter(is_active=True, start_datetime__lte=now, end_datetime__gte=now).count()
    total_attendees = EventRegistration.objects.count()

    # User registrations
    user_registered_ids = set(
        EventRegistration.objects.filter(user=request.user).values_list('event_id', flat=True)
    )
    user_bookmarked_ids = set(
        EventRegistration.objects.filter(user=request.user, is_bookmarked=True).values_list('event_id', flat=True)
    )

    context = {
        'events': events,
        'featured_event': featured,
        'category': category,
        'search_q': search_q,
        'time_filter': time_filter,
        'upcoming_count': upcoming_count,
        'live_count': live_count,
        'total_attendees': total_attendees,
        'user_registered_ids': user_registered_ids,
        'user_bookmarked_ids': user_bookmarked_ids,
        'event_types': Event.EVENT_TYPES,
    }
    return render(request, 'community/events.html', context)


@login_required
@require_POST
def toggle_event_registration(request):
    """AJAX: register / unregister for an event"""
    try:
        event_id = request.POST.get('event_id')
        if not event_id:
            return JsonResponse({'error': 'Event ID required'}, status=400)

        event = get_object_or_404(Event, id=event_id, is_active=True)

        reg, created = EventRegistration.objects.get_or_create(
            event=event, user=request.user
        )
        if not created:
            reg.delete()
            return JsonResponse({
                'success': True,
                'registered': False,
                'registrations_count': event.registrations_count,
                'spots_left': event.spots_left,
            })

        if event.spots_left <= 0:
            reg.delete()
            return JsonResponse({'error': 'No spots left'}, status=400)

        return JsonResponse({
            'success': True,
            'registered': True,
            'registrations_count': event.registrations_count,
            'spots_left': event.spots_left,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def toggle_event_bookmark(request):
    """AJAX: bookmark / un-bookmark an event"""
    try:
        event_id = request.POST.get('event_id')
        if not event_id:
            return JsonResponse({'error': 'Event ID required'}, status=400)

        event = get_object_or_404(Event, id=event_id, is_active=True)

        reg, created = EventRegistration.objects.get_or_create(
            event=event, user=request.user
        )
        reg.is_bookmarked = not reg.is_bookmarked
        reg.save()

        return JsonResponse({
            'success': True,
            'bookmarked': reg.is_bookmarked,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Create the main community view instance
community_view = CommunityView.as_view()