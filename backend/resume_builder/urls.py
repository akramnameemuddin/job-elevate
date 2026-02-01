from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'resume_builder'

urlpatterns = [
    path('', views.resume_dashboard, name='resume_builder'),
    path('create/', views.create_resume, name='create_resume'),
    path('edit/<int:resume_id>/', views.edit_resume, name='edit_resume'),
    path('preview/<int:resume_id>/', views.preview_resume, name='preview_resume'),
    path('download/<int:resume_id>/', views.download_resume, name='download_resume'),
    path('delete/<int:resume_id>/', views.delete_resume, name='delete_resume'),
    path('change-template/<int:resume_id>/', views.change_template, name='change_template'),
]