from django.urls import path
from . import views

app_name = 'recruiter'

urlpatterns = [
    # Dashboard routes
    path('', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('api/stats/', views.get_dashboard_stats, name='get_dashboard_stats'),
    
    # Job routes
    path('api/jobs/', views.get_jobs, name='get_jobs'),
    path('api/jobs/create/', views.create_job, name='create_job'),
    path('api/jobs/<int:job_id>/update/', views.update_job, name='update_job'),
    path('api/jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    
    # Candidate routes
    path('api/candidates/', views.get_candidates, name='get_all_candidates'),
    path('api/candidates/<int:job_id>/', views.get_candidates, name='get_job_candidates'),
    path('api/applications/<int:application_id>/status/', views.update_application_status, name='update_application_status'),
    
    # Profile routes
    path('api/profile/update/', views.update_profile, name='update_profile'),
    
    # Messaging routes
    path('api/applications/<int:application_id>/message/', views.send_message, name='send_message'),
]