# gestion_turnos/urls.py (Proyecto principal)

from django.contrib import admin
from django.urls import path, include # Importamos 'include'

urlpatterns = [
    path('admin/', admin.site.urls),
    # Conecta la URL base ('') a las rutas definidas en turnos/urls.py
    path('', include('turnos.urls')),
]