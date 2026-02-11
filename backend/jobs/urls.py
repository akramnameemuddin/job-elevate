from django.urls import path
from . import views, recommendation_dashboard_views

app_name = 'jobs'

urlpatterns = [
    # Job listings and search
    path('', views.job_listings, name='job_listings'),
    path('search/', views.search_jobs, name='search_jobs'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('job/<int:job_id>/claim-skill/<int:skill_id>/', views.claim_skill_from_job, name='claim_skill_from_job'),
    
    # New Skill-Based Job Recommendations
    path('recommendations/', recommendation_dashboard_views.job_recommendations_dashboard, name='recommendations_dashboard'),
    path('job/<int:job_id>/analysis/', recommendation_dashboard_views.job_detail_with_analysis, name='job_detail_with_analysis'),
    path('job/<int:job_id>/gap-analysis/', recommendation_dashboard_views.skill_gap_analysis, name='skill_gap_analysis'),
    path('job/<int:job_id>/apply-now/', recommendation_dashboard_views.apply_to_job, name='apply_to_job'),
    
    # Applications
    path('job/<int:job_id>/apply/', views.apply_for_job, name='apply_for_job'),
    path('applications/', views.my_applications, name='my_applications'),
    path('application/<int:application_id>/', views.application_detail, name='application_detail'),
    path('application/<int:application_id>/message/', views.send_application_message, name='send_application_message'),
    
    # Bookmarks
    path('job/<int:job_id>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('bookmarks/', views.bookmarked_jobs, name='bookmarked_jobs'),
    
    # Recommendations
    path('recommended/', views.recommended_jobs, name='recommended_jobs'),
    path('preferences/', views.update_job_preferences, name='update_job_preferences'),
    
    # Analytics
    path('analytics/', views.job_analytics, name='job_analytics'),

    
    # API endpoints
    path('api/recommended/', views.api_recommended_jobs, name='api_recommended_jobs'),
]