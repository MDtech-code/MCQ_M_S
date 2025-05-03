from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include('apps.accounts.urls')),
    path('api/',include('apps.content.urls')),
    path('api/',include('apps.examination.urls')),
    path('api/', include('apps.analytics.urls')),
    path('api/',include('apps.common.urls')),
    path('api/',include('apps.nlp_generator.urls')),
    path('api/',include('apps.notifications.urls')),
    path('',include('apps.public.urls')),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)