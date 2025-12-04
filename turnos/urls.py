from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.inicio_gestion, name='inicio'), 
    path('personal/<str:rut>/', views.detalle_personal, name='detalle_personal'), 
    path('programacion/', views.programacion_semanal, name='programacion_semanal_actual'),
     path('programacion/masiva/', views.programar_turnos_masiva, name='programacion_masiva'),
    path('programacion/<str:fecha_str>/', views.programacion_semanal, name='programacion_semanal'),
    path('registro/eliminar/<int:id_registro>/', views.eliminar_registro_turno, name='eliminar_registro_turno'),
    path('asistencia/registro/', views.registrar_asistencia, name='registrar_asistencia'),
    path('asistencia/registrar-llegada/', views.registrar_asistencia_logueado, name='registrar_asistencia_logueado'),
    path('reporte/asistencia/', views.reporte_asistencia, name='reporte_asistencia'),
    path('gestion/turnos/', views.gestion_tipos_turno, name='gestion_tipos_turno'), 
    path('gestion/turnos/editar/<int:id_turno>/', views.gestion_tipos_turno, name='editar_tipo_turno'), 
    path('gestion/turnos/eliminar/<int:id_turno>/', views.eliminar_tipo_turno, name='eliminar_tipo_turno'), 
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('solicitud/crear/', views.crear_solicitud_cambio, name='crear_solicitud_cambio'), 
    path('solicitud/gestion/', views.gestionar_solicitudes, name='gestionar_solicitudes'),
    path('solicitud/procesar/<int:id_solicitud>/<str:accion>/', views.procesar_solicitud, name='procesar_solicitud'),
]