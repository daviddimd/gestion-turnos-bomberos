from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_gestion, name='inicio'), 
    path('personal/<str:rut>/', views.detalle_personal, name='detalle_personal'),
    path('programacion/', views.programacion_semanal, name='programacion_semanal'),
    path('asistencia/registro/', views.registrar_asistencia, name='registrar_asistencia'),
    path('reporte/asistencia/', views.reporte_asistencia, name='reporte_asistencia'),
    path('programacion/masiva/', views.programar_turnos_masiva, name='programacion_masiva'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
]