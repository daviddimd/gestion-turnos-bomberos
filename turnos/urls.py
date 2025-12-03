from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_gestion, name='inicio'), 
    path('personal/<str:rut>/', views.detalle_personal, name='detalle_personal'),
    path('programacion/', views.programacion_semanal, name='programacion_semanal'),
    path('reporte/asistencia/', views.reporte_asistencia, name='reporte_asistencia'),
    path('programacion/masiva/', views.programar_turnos_masiva, name='programacion_masiva'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('registro/eliminar/<int:id_registro>/', views.eliminar_registro_turno, name='eliminar_registro_turno'),
    path('programacion/', views.programacion_semanal, name='programacion_semanal_actual'),
    path('programacion/<str:fecha_str>/', views.programacion_semanal, name='programacion_semanal'),
    path('asistencia/registrar-llegada/', views.registrar_asistencia_logueado, name='registrar_asistencia_logueado'),
]