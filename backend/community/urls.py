from django.urls import path
from .views import CommunityView
from . import views

app_name = 'community'

urlpatterns = [
    # Single main community view that handles all sections
    path('', CommunityView.as_view(), name='community'),
    
    # AJAX endpoints for interactions
    path('ajax/toggle-like/', views.toggle_like, name='toggle_like'),
    path('ajax/toggle-follow/', views.toggle_follow, name='toggle_follow'),
    path('ajax/delete-post/', views.delete_post, name='delete_post'),
    path('ajax/delete-comment/', views.delete_comment, name='delete_comment'),
    path('ajax/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]