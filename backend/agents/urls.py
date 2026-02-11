from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    path('career-coach/', views.career_guidance_view, name='career_guidance'),
    path('recruiter/', views.recruiter_agent_view, name='recruiter_agent'),
    path('agents-demo/', views.multi_agent_demo_view, name='multi_agent_demo'),
    path('run/<int:run_id>/', views.agent_run_detail_view, name='agent_run_detail'),
]
