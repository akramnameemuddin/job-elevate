from django.urls import path
from .views import assessments

app_name = 'assessments'

urlpatterns = [
    path('', assessments, name='assessment')
]
