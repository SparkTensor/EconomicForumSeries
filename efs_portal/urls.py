# event_manager/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
      
    # --- ADD THIS BLOCK FOR YOUR API ---
    # All API URLs will be prefixed with /api/v1/
    path('api/v1/', include('core.api_urls')),
]


# --- Add this line at the bottom ---
# This serves static and media files only during development (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Optional, for collectstatic testing