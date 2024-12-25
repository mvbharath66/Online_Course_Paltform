
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('onlinecourse.urls')),
    #path('api/', include('onlinecourse.urls_api')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)