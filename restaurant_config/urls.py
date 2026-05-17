from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from core.views import home_view, contact_view
urlpatterns=[
    path('', home_view, name='home'),
    path('contact/', contact_view, name='contact'),

    path('django-admin/',admin.site.urls),
    
    path('accounts/',include('accounts.urls')),
    path('menu/',include('menu.urls')),
    path('orders/',include('orders.urls')),
    path('reservations/',include('reservations.urls')),
    path('staff/',include('staffops.urls')),
    path('admin-panel/',include('admin_panel.urls'))]
    
if settings.DEBUG: urlpatterns+=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
