from django.urls import path
from .views import learning

app_name = 'learning'

urlpatterns = [
    path('', learning, name='learning'),
]
