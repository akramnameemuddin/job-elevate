from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # Home and listing pages
    path('', views.CommunityHomeView.as_view(), name='home'),
    path('my-posts/', views.my_posts, name='my_posts'),
    path('notifications/', views.notifications_list, name='notifications'),
    
    # Post CRUD operations
    path('post/create/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/<slug:slug>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('post/<slug:slug>/delete/', views.delete_post, name='post_delete'),
    
    # Comment operations
    path('post/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('comment/<uuid:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    # AJAX endpoints
    path('ajax/toggle-like/', views.toggle_like, name='toggle_like'),
    path('ajax/toggle-follow/', views.toggle_follow, name='toggle_follow'),
    
    # Tag-based filtering
    path('tag/<slug:slug>/', views.TagPostsView.as_view(), name='tag_posts'),
    
    # User profiles
    path('user/<str:username>/', views.user_profile, name='user_profile'),
]