from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # REST API endpoints
    # path('api/', include('assessments.api_urls')),  # Temporarily disabled
    
    # Traditional web views
    path('', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('assessments/', include('assessments.urls')),
    path('learning/', include('learning.urls')),
    path('community/', include('community.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('recruiter/', include('recruiter.urls')),
    path('resume_builder/', include('resume_builder.urls')),
    path('ai/', include(('agents.urls', 'agents'), namespace='agents')),
]

# Media and static file serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
