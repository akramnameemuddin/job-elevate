from django.urls import path
from .views import community

app_name = 'community'

urlpatterns = [
    path('', community, name='home'),
]