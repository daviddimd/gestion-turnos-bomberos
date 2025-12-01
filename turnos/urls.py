# turnos/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Asigna la URL raíz de la aplicación ('') a la función 'inicio_gestion'
    path('', views.inicio_gestion, name='inicio'), 
    path('personal/<str:rut>/', views.detalle_personal, name='detalle_personal'),
    path('programacion/', views.programacion_semanal, name='programacion_semanal'),
    path('asistencia/registro/', views.registrar_asistencia, name='registrar_asistencia'),
]