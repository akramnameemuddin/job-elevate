from django.urls import path
from .views import dashboard,profile
from django.conf import settings
from django.conf.urls.static import static

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard, name='home'),
    path('profile/', profile, name='profile'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
