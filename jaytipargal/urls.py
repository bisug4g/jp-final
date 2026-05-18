"""
URL configuration for jaytipargal project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from datetime import datetime

def root_health_check(request):
    """
    Root-level health check for Kubernetes probes.
    CRITICAL: Must respond immediately without any DB operations.
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
    }, status=200)

@csrf_exempt
def api_not_found(request):
    """
    Catch-all for /api requests - this Django app doesn't use /api prefix.
    Returns proper JSON response instead of 404 HTML.
    """
    return JsonResponse({
        'error': 'API endpoint not found',
        'message': 'This application does not use /api prefix. Please check documentation.',
        'available_endpoints': ['/health', '/notes/', '/diary/', '/goals/', '/astro/', '/ai-chat/']
    }, status=404)

urlpatterns = [
    # Health check at root level - responds BEFORE any middleware/DB
    path('health', root_health_check, name='root_health'),
    path('health/', root_health_check, name='root_health_slash'),
    
    # Robots.txt - block crawlers (personal app)
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    
    # Catch-all for /api requests (reduces 404 noise from scanners)
    path('api', api_not_found, name='api_not_found'),
    path('api/', api_not_found, name='api_not_found_slash'),
    
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('notes/', include('notes.urls')),
    path('diary/', include('diary.urls')),
    path('goals/', include('goals.urls')),
    path('astro/', include('astro.urls')),
    path('ai-chat/', include('ai_chat.urls')),
    path('tangred/', include('tangred.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
