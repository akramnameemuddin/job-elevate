from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def web_app_manifest(_request):
    """Serve manifest from app origin to avoid cross-origin manifest fetch issues."""
    return JsonResponse(
        {
            "name": "JobElevate",
            "short_name": "JobElevate",
            "description": "Elevate Your Career Journey with AI-powered job matching, skill assessments, and personalized learning paths",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#3b82f6",
            "orientation": "portrait-primary",
            "scope": "/",
            "lang": "en",
            "categories": ["business", "productivity", "education"],
            "icons": [
                {
                    "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='40' fill='%233b82f6'/%3E%3Ctext x='50' y='60' text-anchor='middle' fill='white' font-size='40' font-family='Arial'%3EJ%3C/text%3E%3C/svg%3E",
                    "sizes": "192x192",
                    "type": "image/svg+xml",
                    "purpose": "any maskable",
                },
                {
                    "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='40' fill='%233b82f6'/%3E%3Ctext x='50' y='60' text-anchor='middle' fill='white' font-size='40' font-family='Arial'%3EJ%3C/text%3E%3C/svg%3E",
                    "sizes": "512x512",
                    "type": "image/svg+xml",
                    "purpose": "any maskable",
                },
            ],
            "shortcuts": [
                {
                    "name": "Job Search",
                    "short_name": "Jobs",
                    "description": "Find your perfect job match",
                    "url": "/jobs/",
                },
                {
                    "name": "Resume Builder",
                    "short_name": "Resume",
                    "description": "Build professional resumes",
                    "url": "/resume_builder/",
                },
                {
                    "name": "Dashboard",
                    "short_name": "Dashboard",
                    "description": "Your career dashboard",
                    "url": "/dashboard/",
                },
            ],
        },
        content_type="application/manifest+json",
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('manifest.json', web_app_manifest, name='web_app_manifest'),
    
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
