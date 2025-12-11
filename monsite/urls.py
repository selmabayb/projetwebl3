# monsite/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from garage.views import home

urlpatterns = [
    # Page d'accueil
    path('', home, name='home'),

    path('admin/', admin.site.urls),

    # Authentification Django
    path('accounts/', include('django.contrib.auth.urls')),

    # Applications
    path('vehicles/', include('garage.vehicles.urls')),
    path('cases/', include('garage.cases.urls')),
    path('', include('garage.accounts.urls')),
    path('quotes/', include('garage.quotes.urls')),
    path('appointments/', include('garage.appointments.urls')),
    path('billing/', include('garage.billing.urls')),
    path('notifications/', include('garage.notifications.urls')),
]

# Gestion des fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
