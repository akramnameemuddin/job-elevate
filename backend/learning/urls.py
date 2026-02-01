from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.learning_dashboard, name='learning_dashboard'),
    path('paths/', views.learning_dashboard, name='learning_paths_dashboard'),  # Alias for consistency
    path('gaps/', views.skill_gaps, name='skill_gaps'),
    path('gaps/analyze/', views.analyze_job_gaps, name='analyze_job_gaps'),
    path('path/<int:path_id>/', views.learning_path_detail, name='learning_path_detail'),
    path('path/generate/', views.generate_learning_path, name='generate_learning_path'),
    path('courses/', views.course_catalog, name='course_catalog'),
    path('courses/enroll/', views.enroll_course, name='enroll_course'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('progress/update/', views.update_course_progress, name='update_course_progress'),
]
