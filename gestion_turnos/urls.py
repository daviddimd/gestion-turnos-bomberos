from django.contrib import admin
from django.urls import path, include 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Carga todas las rutas de la app 'turnos' en la raíz (ej. /programacion/)
    path('', include('turnos.urls')),
    
    # Rutas de autenticación de Django (ej. /accounts/login/)
    path('accounts/', include('django.contrib.auth.urls')),
]