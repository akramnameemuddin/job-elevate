"""
URL patterns for skill assessments
Entry point: Job detail page → "Fill Gap" button
"""
from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    # Default landing: Skill Intake Dashboard (direct access)
    path('', views.skill_intake_dashboard, name='skill_intake_dashboard'),
    
    # Job-specific skill gap analysis
    path('job/<int:job_id>/gaps/', 
         views.job_skill_gap_analysis, 
         name='job_skill_gap_analysis'),
    
    # Start assessment from job gap analysis (MAIN ENTRY POINT)
    path('start-from-job/<int:job_id>/<int:skill_id>/', 
         views.start_assessment_from_job, 
         name='start_assessment_from_job'),
    
    # Start assessment directly (alternative entry point)
    path('start/<int:skill_id>/', 
         views.start_assessment_direct, 
         name='start_assessment_direct'),
    
    # Take assessment (questions display)
    path('take/<int:attempt_id>/', 
         views.take_assessment, 
         name='take_assessment'),
    
    # Submit single answer (AJAX)
    path('submit-answer/<int:attempt_id>/', 
         views.submit_answer, 
         name='submit_answer'),
    
    # Submit complete assessment
    path('submit/<int:attempt_id>/', 
         views.submit_assessment, 
         name='submit_assessment'),
    
    # View results
    path('result/<int:attempt_id>/', 
         views.assessment_result, 
         name='assessment_result'),
]
