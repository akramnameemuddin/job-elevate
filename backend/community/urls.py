from django.urls import path
from .views import CommunityView
from . import views

app_name = 'community'

urlpatterns = [
    # Single main community view that handles all sections
    path('', CommunityView.as_view(), name='community'),
    
    # AJAX endpoints for interactions - fix URLs to match JavaScript calls
    path('toggle-like/', views.toggle_like, name='toggle_like'),
    path('toggle-follow/', views.toggle_follow, name='toggle_follow'),
    path('delete-post/', views.delete_post, name='delete_post'),
    path('delete-comment/', views.delete_comment, name='delete_comment'),
    path('mark-all-notifications-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]