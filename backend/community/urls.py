from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # Main community view
    path('', views.community_view, name='community'),
    
    # Events
    path('events/', views.events_view, name='events'),
    path('toggle-event-registration/', views.toggle_event_registration, name='toggle_event_registration'),
    path('toggle-event-bookmark/', views.toggle_event_bookmark, name='toggle_event_bookmark'),
    
    # AJAX endpoints for interactions - fix URLs to match JavaScript calls
    path('toggle-like/', views.toggle_like, name='toggle_like'),
    path('toggle-follow/', views.toggle_follow, name='toggle_follow'),
    path('delete-post/', views.delete_post, name='delete_post'),
    path('delete-comment/', views.delete_comment, name='delete_comment'),
    path('mark-all-notifications-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Direct access URLs (redirects to main view with params)
    path('post/<slug:slug>/', views.post_detail_view, name='post_detail'),
    path('post/<slug:slug>/edit/', views.edit_post_view, name='edit_post'),
    path('user/<str:username>/', views.user_profile_view, name='user_profile'),
    path('tag/<slug:slug>/', views.tag_posts_view, name='tag_posts'),
]