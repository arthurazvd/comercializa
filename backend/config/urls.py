from django.conf import settings
from django.contrib import admin
from django.http import FileResponse
from django.urls import include, path, re_path
from core.auth_views import HealthView


def frontend_index(request):
    return FileResponse((settings.FRONTEND_DIST / 'index.html').open('rb'), content_type='text/html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('health', HealthView.as_view(), name='health'),
    path('health/', HealthView.as_view()),
]
if settings.FRONTEND_DIST.is_dir():
    urlpatterns += [re_path(r'^(?!(?:api|admin|static|assets)(?:/|$)).*$', frontend_index)]
