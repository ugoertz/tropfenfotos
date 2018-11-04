"""droplets URL Configuration
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from shoots import views as shoots_views


urlpatterns = [
    path('valves/', shoots_views.valves),
    path('flashair/', shoots_views.flashair),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

