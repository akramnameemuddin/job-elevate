from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from . import ai_views

app_name = 'resume_builder'

urlpatterns = [
    path('', views.resume_dashboard, name='resume_builder'),
    path('dashboard/', views.resume_dashboard, name='dashboard'),
    path('create/', views.create_resume, name='create_resume'),
    path('edit/<int:resume_id>/', views.edit_resume, name='edit_resume'),
    path('preview/<int:resume_id>/', views.preview_resume, name='preview_resume'),
    path('download/<int:resume_id>/', views.download_resume, name='download_resume'),
    path('delete/<int:resume_id>/', views.delete_resume, name='delete_resume'),
    path('change-template/<int:resume_id>/', views.change_template, name='change_template'),
    path('analyzer/<int:job_id>/', views.resume_analyzer, name='resume_analyzer'),

    # Tailored resume preview & download
    path('tailored/preview/<int:tailored_id>/', views.preview_tailored_resume, name='preview_tailored'),
    path('tailored/download/<int:tailored_id>/', views.download_tailored_resume, name='download_tailored'),

    # AI resume tailoring flow
    path('ai/tailor/<int:job_id>/', ai_views.tailor_for_job, name='tailor_for_job'),
    path('ai/review/<int:tailored_id>/', ai_views.ai_review, name='ai_review'),
    path('ai/accept/<int:tailored_id>/', ai_views.accept_suggestion, name='accept_suggestion'),
    path('ai/accept-all/<int:tailored_id>/', ai_views.accept_all_suggestions, name='accept_all'),
    path('ai/finalize/<int:tailored_id>/', ai_views.apply_and_finalize, name='apply_finalize'),
    path('ai/regenerate/<int:tailored_id>/', ai_views.regenerate_suggestions, name='regenerate'),
]