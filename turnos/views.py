from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Sum, Q, F
from django.db import models
from .forms import ProgramacionMasivaForm
from django.db import IntegrityError
from .models import Persona, Turno, RegistroTurno, Estado
from django.contrib.auth.decorators import login_required, user_passes_test
import datetime
import pytz

def inicio_gestion(request):
    """Muestra un resumen de las personas y los turnos."""
    personal = Persona.objects.all().order_by('Apellido')
    turnos_programados = Turno.objects.all()

    import datetime
    hoy = datetime.date.today()
    registros_hoy = RegistroTurno.objects.filter(Fecha=hoy).count()

    context = {
        'titulo': 'Panel de Gestión de Turnos',
        'personal': personal,
        'turnos_programados': turnos_programados,
        'registros_hoy': registros_hoy,
        'fecha_hoy': hoy,
    }

    return render(request, 'turnos/inicio.html', context)

def detalle_personal(request, rut):
    """Muestra la información y el historial de turnos de una persona específica."""
    persona = get_object_or_404(Persona, Rut=rut)
    historial_turnos = RegistroTurno.objects.filter(Rut=persona).order_by('-Fecha')
    
    context = {
        'persona': persona,
        'historial_turnos': historial_turnos,
        'titulo': f'Historial de {persona.Nombre} {persona.Apellido}'
    }
    
    return render(request, 'turnos/detalle_personal.html', context)


def programacion_semanal(request):
    """Muestra la programación de turnos para la semana actual."""
    hoy = datetime.date.today()
    dia_inicio_semana = hoy - datetime.timedelta(days=hoy.weekday())
    dia_fin_semana = dia_inicio_semana + datetime.timedelta(days=6)
    
    rango_dias = [dia_inicio_semana + datetime.timedelta(days=i) for i in range(7)]

    registros_semana = RegistroTurno.objects.filter(
        Fecha__gte=dia_inicio_semana,  
        Fecha__lte=dia_fin_semana      
    ).order_by('Fecha', 'ID_turno__Hora_inicio')

    programacion_por_dia = {}
    for dia in rango_dias:
        registros_del_dia = [r for r in registros_semana if r.Fecha == dia]
        turnos_agrupados = {}
        for registro in registros_del_dia:
            tipo_turno = registro.ID_turno.Tipo_turno
            if tipo_turno not in turnos_agrupados:
                turnos_agrupados[tipo_turno] = []
            turnos_agrupados[tipo_turno].append(registro)

        programacion_por_dia[dia] = turnos_agrupados

    context = {
        'titulo': f'Programación Semanal ({dia_inicio_semana} al {dia_fin_semana})',
        'rango_dias': rango_dias,
        'programacion_por_dia': programacion_por_dia,
        'hoy': hoy,
    }
    
    return render(request, 'turnos/programacion_semanal.html', context)



ZONA_HORARIA = pytz.timezone('America/Santiago') 

def registrar_asistencia(request):
    """Muestra el formulario y procesa el registro de asistencia."""
    
    context = {'mensaje': None, 'clase': ''}
    
    if request.method == 'POST':
        rut_ingresado = request.POST.get('rut').strip()
        
        try:
            persona = Persona.objects.get(Rut=rut_ingresado)
        except Persona.DoesNotExist:
            context['mensaje'] = "Error: El RUT ingresado no se encuentra en el registro de personal."
            context['clase'] = 'error'
            return render(request, 'turnos/registrar_asistencia.html', context)

        hoy = datetime.date.today()
        registro = RegistroTurno.objects.filter(Rut=persona, Fecha=hoy).first()

        if not registro:
            context['mensaje'] = f"Error: No hay turno programado para {persona.Nombre} hoy ({hoy})."
            context['clase'] = 'error'
            return render(request, 'turnos/registrar_asistencia.html', context)
        
        hora_actual = datetime.datetime.now(ZONA_HORARIA).time()
        
        hora_inicio_programada = registro.ID_turno.Hora_inicio
        
        llegada = datetime.datetime.combine(hoy, hora_actual)
        programada = datetime.datetime.combine(hoy, hora_inicio_programada)
        diferencia = llegada - programada

        minutos_tardanza = 0
        estado_id = 1 # 1 es 'Normal'
        
        if diferencia > datetime.timedelta(minutes=0):
            minutos_tardanza = int(diferencia.total_seconds() / 60)
            if minutos_tardanza > 5:
                 estado_id = 2
            else:
                 estado_id = 1

        registro.Hora_llegada_real = hora_actual
        registro.Minutos_tardanza = minutos_tardanza
        registro.ID_estado = Estado.objects.get(ID_estado=estado_id)
        registro.save()
        
        context['mensaje'] = f"✅ Asistencia registrada para {persona.Nombre} {persona.Apellido} ({registro.ID_turno.Tipo_turno}). Estado: {registro.ID_estado.Nombre_estado}."
        context['clase'] = 'exito'

        return render(request, 'turnos/registrar_asistencia.html', context)

    return render(request, 'turnos/registrar_asistencia.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reporte_asistencia(request):
    """Muestra un reporte consolidado de asistencia basado en un rango de fechas."""

    hoy = datetime.date.today()
    fecha_inicio_defecto = hoy.replace(day=1) 
    fecha_fin_defecto = hoy
    
    fecha_inicio_str = request.GET.get('fecha_inicio', str(fecha_inicio_defecto))
    fecha_fin_str = request.GET.get('fecha_fin', str(fecha_fin_defecto))
    
    try:
        fecha_inicio = datetime.datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_inicio = fecha_inicio_defecto
        fecha_fin = fecha_fin_defecto

    personal = Persona.objects.all().order_by('Apellido')
    
    reporte_consolidado = []

    for persona in personal:
        registros = RegistroTurno.objects.filter(
            Rut=persona, 
            Fecha__range=[fecha_inicio, fecha_fin]
        )

        estadisticas = registros.aggregate(
            total_turnos=Count('ID_registro'),
            normal=Count('ID_registro', filter=models.Q(ID_estado__ID_estado=1)),
            atraso=Count('ID_registro', filter=models.Q(ID_estado__ID_estado=2)),
            ausente=Count('ID_registro', filter=models.Q(ID_estado__ID_estado=3)),
            minutos_tardanza_total=Sum('Minutos_tardanza')
        ) 
        reporte_consolidado.append({
            'persona': persona,
            'stats': estadisticas,
        })

    context = {
        'titulo': 'Reporte Consolidado de Asistencia',
        'reporte_consolidado': reporte_consolidado,
        'fecha_inicio_str': fecha_inicio_str,
        'fecha_fin_str': fecha_fin_str,
    }
    
    return render(request, 'turnos/reporte_asistencia.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def programar_turnos_masiva(request):
    """Vista para generar multiples registros de turno en un rango de fechas."""
    
    mensaje = None
    
    if request.method == 'POST':
        form = ProgramacionMasivaForm(request.POST)
        
        if form.is_valid():
            persona = form.cleaned_data['persona']
            tipo_turno = form.cleaned_data['tipo_turno']
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            diferencia = fecha_fin - fecha_inicio
            dias_programados = 0
            
            for i in range(diferencia.days + 1):
                fecha_actual = fecha_inicio + datetime.timedelta(days=i)
                
                try:
                    RegistroTurno.objects.create(
                        Fecha=fecha_actual,
                        Rut=persona,
                        ID_turno=tipo_turno,
                        ID_estado_id=1 
                    )
                    dias_programados += 1
                except IntegrityError:
                   
                    pass 

            mensaje = f"✅ Éxito: Se programaron {dias_programados} turnos para {persona.Apellido} ({tipo_turno.Tipo_turno}) del {fecha_inicio} al {fecha_fin}."

            form = ProgramacionMasivaForm() 
            
    else:

        form = ProgramacionMasivaForm()

    context = {
        'titulo': 'Programación Masiva de Turnos',
        'form': form,
        'mensaje': mensaje
    }
    
    return render(request, 'turnos/programacion_masiva.html', context)

@login_required
def mi_perfil(request):
    """Muestra el historial de turnos de la persona logueada."""

    usuario_django = request.user
    
    try: 
        rut_usuario = usuario_django.username
        persona = Persona.objects.get(Rut=rut_usuario)
        historial_turnos = RegistroTurno.objects.filter(Rut=persona).order_by('-Fecha')
        
    except Persona.DoesNotExist:
        return render(request, 'turnos/error_perfil.html', {'mensaje': 'Su usuario no está asociado a ningún bombero en el registro.'})

    context = {
        'persona': persona,
        'historial_turnos': historial_turnos,
        'titulo': f'Mi Perfil y Historial de {persona.Nombre}',
    }
    
    return render(request, 'turnos/mi_perfil.html', context)