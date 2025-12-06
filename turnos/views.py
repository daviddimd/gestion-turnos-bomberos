from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth import authenticate
from django.contrib import messages
from django.db.models import Count, Sum, Q, F
from django.db import models
from django.http import HttpResponseRedirect
from .models import Persona, Turno, RegistroTurno, Estado, SolicitudCambio
from .forms import ProgramacionMasivaForm, SolicitudCambioForm, TurnoForm
import datetime
import pytz 

ZONA_HORARIA = pytz.timezone('America/Santiago') 

def get_greeting(hour):
    if 6 <= hour < 12:
        return "Buenos días"
    elif 12 <= hour < 19:
        return "Buenas tardes"
    else:
        return "Buenas noches"

@login_required
def inicio_gestion(request):
    
    ahora = datetime.datetime.now(ZONA_HORARIA)
    hoy = ahora.date()
    hora_actual_time = ahora.time()
    saludo = get_greeting(ahora.hour)
    
    personal = Persona.objects.all().order_by('Apellido')
    turnos_programados_tipos = Turno.objects.all()
    registros_hoy = RegistroTurno.objects.filter(Fecha=hoy).order_by('ID_turno__Hora_inicio')
    
    operador_persona = None
    nombre_usuario = request.user.get_username()
    siguiente_turno_qs = None
    solicitudes_pendientes = 0
    estado_operador = {'mensaje': "Error de perfil: El usuario logueado no tiene un perfil de bombero asociado (Persona).", 'clase': 'error', 'minutos': 0, 'mostrar_boton': False}

    if request.user.is_superuser or request.user.has_perm('turnos.view_solicitudcambio'):
        solicitudes_pendientes = SolicitudCambio.objects.filter(estado='Pendiente').count()

    try:
        operador_persona = request.user.persona 
        nombre_usuario = operador_persona.Nombre
        
        siguiente_turno_qs = registros_hoy.filter(
            ID_turno__Hora_inicio__gte=hora_actual_time
        ).order_by('ID_turno__Hora_inicio').first()
        
        turnos_del_dia = registros_hoy.filter(Rut=operador_persona)
        
        turno_relevante = turnos_del_dia.filter(
            Hora_llegada_real__isnull=True
        ).order_by('ID_turno__Hora_inicio').first()
        
        if turno_relevante:
            hora_inicio = turno_relevante.ID_turno.Hora_inicio
            
            inicio_dt_puro = datetime.datetime.combine(hoy, hora_inicio) 
            ahora_dt_puro = datetime.datetime.now()
            
            estado_operador['mostrar_boton'] = True 
            
            if ahora_dt_puro <= inicio_dt_puro:
                diferencia_hasta_inicio = inicio_dt_puro - ahora_dt_puro
                minutos_restantes = int(diferencia_hasta_inicio.total_seconds() / 60)
                
                estado_operador['mensaje'] = f"Estás a tiempo. Tu turno comienza en {minutos_restantes} min ({hora_inicio.strftime('%H:%M')})."
                estado_operador['clase'] = 'normal'
            else:
                diferencia = ahora_dt_puro - inicio_dt_puro
                minutos_tardanza = int(diferencia.total_seconds() / 60)
                
                estado_operador['mostrar_boton'] = True
                
                if minutos_tardanza < 300:
                    estado_operador['mensaje'] = f"¡Alerta! Te encuentras con <strong>atraso de {minutos_tardanza} min</strong>. Tu turno comenzó a las {hora_inicio.strftime('%H:%M')}."
                    estado_operador['clase'] = 'alerta'
                else:
                    estado_operador['mensaje'] = f"⚠️ Tienes un turno pendiente de {hora_inicio.strftime('%H:%M')} que no has registrado. Regístrelo."
                    estado_operador['clase'] = 'error'
        
        elif turnos_del_dia.exists():
            estado_operador['mensaje'] = "Asistencia registrada para hoy. ¡Gracias!"
            estado_operador['clase'] = 'exito'
            estado_operador['mostrar_boton'] = False 

        else:
            estado_operador['mensaje'] = "No tienes turno programado pendiente para registrar hoy."
            estado_operador['clase'] = 'info'
            estado_operador['mostrar_boton'] = False


    except Persona.DoesNotExist:
        siguiente_turno_qs = None 
        pass 
    
    context = {
        'titulo': 'Panel de Gestión de Turnos',
        'personal': personal,
        'turnos_programados_tipos': turnos_programados_tipos,
        'saludo': saludo,
        'nombre_usuario': nombre_usuario,
        'hora_actual': ahora,
        'fecha_hoy': hoy,
        'siguiente_turno': siguiente_turno_qs,
        'registros_hoy': registros_hoy,
        'estado_operador': estado_operador,
        'solicitudes_pendientes': solicitudes_pendientes,
    }
    
    return render(request, 'turnos/inicio.html', context)

@login_required
def detalle_personal(request, rut):
    persona = get_object_or_404(Persona, Rut=rut)
    historial_turnos = RegistroTurno.objects.filter(Rut=persona).order_by('-Fecha')
    
    context = {
        'persona': persona,
        'historial_turnos': historial_turnos,
        'titulo': f'Historial de {persona.Nombre} {persona.Apellido}'
    }
    
    return render(request, 'turnos/detalle_personal.html', context)

@login_required
def programacion_semanal(request, fecha_str=None):
    
    if fecha_str:
        try:
            fecha_referencia = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_referencia = datetime.date.today()
    else:
        fecha_referencia = datetime.date.today()

    dia_inicio_semana = fecha_referencia - datetime.timedelta(days=fecha_referencia.weekday())
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

    semana_anterior = dia_inicio_semana - datetime.timedelta(days=7)
    semana_siguiente = dia_inicio_semana + datetime.timedelta(days=7)
        
    context = {
        'titulo': f'Programación Semanal ({dia_inicio_semana} al {dia_fin_semana})',
        'rango_dias': rango_dias,
        'programacion_por_dia': programacion_por_dia,
        'hoy': datetime.date.today(),
        'semana_anterior': semana_anterior.strftime('%Y-%m-%d'),
        'semana_siguiente': semana_siguiente.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'turnos/programacion_semanal.html', context)

def registrar_asistencia(request):
    
    context = {'mensaje': None, 'clase': ''}
    
    if request.method == 'POST':
        rut_ingresado = request.POST.get('rut').strip()
        clave_ingresada = request.POST.get('password')
        
        user = authenticate(request, username=rut_ingresado, password=clave_ingresada)
        
        if user is None:
            context['mensaje'] = "Error: RUT o Clave de acceso incorrectos. Verifique sus credenciales."
            context['clase'] = 'error'
            return render(request, 'turnos/registrar_asistencia.html', context)
            
        try:
            persona = Persona.objects.get(Rut=rut_ingresado)
        except Persona.DoesNotExist:
            context['mensaje'] = "Error: El usuario autenticado no está asociado a un registro de bombero."
            context['clase'] = 'error'
            return render(request, 'turnos/registrar_asistencia.html', context)
        
        hoy = datetime.date.today()
        
        registro = RegistroTurno.objects.filter(Rut=persona, Fecha=hoy, Hora_llegada_real__isnull=True).order_by('ID_turno__Hora_inicio').first()

        if not registro:
            context['mensaje'] = f"Error: No hay turno programado pendiente para {persona.Nombre} hoy ({hoy})."
            context['clase'] = 'error'
            return render(request, 'turnos/registrar_asistencia.html', context)
        
        ZONA_HORARIA = pytz.timezone('America/Santiago') 
        hora_actual = datetime.datetime.now().time()
        hora_inicio_programada = registro.ID_turno.Hora_inicio
        
        llegada = datetime.datetime.combine(hoy, hora_actual)
        programada = datetime.datetime.combine(hoy, hora_inicio_programada)
        
        diferencia = llegada.replace(tzinfo=None) - programada.replace(tzinfo=None)

        minutos_tardanza = 0
        estado_id = 1 
        
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
        
        messages.success(request, f"Asistencia registrada para {persona.Nombre} {persona.Apellido}. Estado: {registro.ID_estado.Nombre_estado}.")
        return redirect('mi_perfil') 
    
    return render(request, 'turnos/registrar_asistencia.html', context)

@login_required
def registrar_asistencia_logueado(request):
    
    rut_usar = request.user.username
    hoy = datetime.date.today()
    
    try:
        persona = get_object_or_404(Persona, Rut=rut_usar)
        
        registro = RegistroTurno.objects.filter(Rut=persona, Fecha=hoy, Hora_llegada_real__isnull=True).order_by('ID_turno__Hora_inicio').first()

        if not registro:
            messages.error(request, f"Error: No hay turno programado pendiente para {persona.Nombre} hoy ({hoy}).")
            return redirect('mi_perfil') 
        
        ZONA_HORARIA = pytz.timezone('America/Santiago') 
        hora_actual = datetime.datetime.now().time()
        hora_inicio_programada = registro.ID_turno.Hora_inicio
        
        llegada = datetime.datetime.combine(hoy, hora_actual)
        programada = datetime.datetime.combine(hoy, hora_inicio_programada)
        
        diferencia = llegada.replace(tzinfo=None) - programada.replace(tzinfo=None)

        minutos_tardanza = 0
        estado_id = 1 
        
        if diferencia > datetime.timedelta(minutes=0):
            minutos_tardanza = int(diferencia.total_seconds() / 60)
            if minutos_tardanza > 5:
                estado_id = 2

        registro.Hora_llegada_real = hora_actual
        registro.Minutos_tardanza = minutos_tardanza
        registro.ID_estado = Estado.objects.get(ID_estado=estado_id) 
        registro.save()
        
        messages.success(request, f"Llegada registrada: {persona.Nombre}. Estado: {registro.ID_estado.Nombre_estado}.")
        
        return redirect('mi_perfil') 

    except Exception:
        messages.error(request, "Error interno al procesar el registro de asistencia.")
        return redirect('mi_perfil')

@login_required
@permission_required('turnos.view_registroturno', raise_exception=True)
def reporte_asistencia(request):
    
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

    reporte_consolidado = Persona.objects.filter(
        registroturno__Fecha__range=[fecha_inicio, fecha_fin] 
    ).annotate(
        total_turnos=Count('registroturno', distinct=True),
        normal=Count(
            'registroturno', 
            filter=Q(registroturno__Fecha__range=[fecha_inicio, fecha_fin], 
                     registroturno__ID_estado__ID_estado=1),
            distinct=True
        ),
        atraso=Count(
            'registroturno', 
            filter=Q(registroturno__Fecha__range=[fecha_inicio, fecha_fin], 
                     registroturno__ID_estado__ID_estado=2),
            distinct=True
        ),
        ausente=Count(
            'registroturno', 
            filter=Q(registroturno__Fecha__range=[fecha_inicio, fecha_fin], 
                     registroturno__ID_estado__ID_estado=3),
            distinct=True
        ),
        minutos_tardanza_total=Sum(
            'registroturno__Minutos_tardanza', 
            filter=Q(registroturno__Fecha__range=[fecha_inicio, fecha_fin])
        )
    ).order_by('Apellido')
    
    context = {
        'titulo': 'Reporte Consolidado de Asistencia',
        'reporte_consolidado': reporte_consolidado,
        'fecha_inicio_str': fecha_inicio_str,
        'fecha_fin_str': fecha_fin_str,
    }
    
    return render(request, 'turnos/reporte_asistencia.html', context)

@login_required
@permission_required('turnos.add_registroturno', raise_exception=True)
def programar_turnos_masiva(request):
    
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
                except Exception:
                    pass 

            messages.success(request, f"Éxito: Se programaron {dias_programados} turnos para {persona.Apellido} ({tipo_turno.Tipo_turno}) del {fecha_inicio} al {fecha_fin}.")
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
    
    usuario_django = request.user
    
    try:
        operador_persona = usuario_django.persona 
        historial_turnos = RegistroTurno.objects.filter(Rut=operador_persona).order_by('-Fecha')
        solicitudes_del_usuario = SolicitudCambio.objects.filter(persona_solicitante=operador_persona).order_by('-fecha_solicitud')
        
    except Persona.DoesNotExist:
        return render(request, 'turnos/error_perfil.html', {'mensaje': 'Error de perfil: Su usuario no está asociado a un bombero en el registro.'})

    context = {
        'persona': operador_persona,
        'historial_turnos': historial_turnos,
        'titulo': f'Mi Perfil y Historial de {operador_persona.Nombre}',
        'solicitudes_del_usuario': solicitudes_del_usuario,
    }
    
    return render(request, 'turnos/mi_perfil.html', context)

@login_required
@permission_required('turnos.delete_registroturno', raise_exception=True)
def eliminar_registro_turno(request, id_registro):
    
    registro = get_object_or_404(RegistroTurno, ID_registro=id_registro)
    url_anterior = request.META.get('HTTP_REFERER', '/')
    
    registro.delete()
    messages.success(request, f'Registro de turno ID {id_registro} eliminado correctamente.')
    
    return HttpResponseRedirect(url_anterior)

@login_required
@permission_required('turnos.change_turno', raise_exception=True)
def gestion_tipos_turno(request, id_turno=None):
    
    turno_a_editar = get_object_or_404(Turno, ID_turno=id_turno) if id_turno else None
    
    if request.method == 'POST':
        form = TurnoForm(request.POST, instance=turno_a_editar)
        if form.is_valid():
            
            turno_guardado = form.save(commit=False)
            
            turno_guardado.Duracion_horas = form.cleaned_data['Duracion_horas']
            
            turno_guardado.save()
            
            if turno_a_editar:
                messages.success(request, f"Tipo de turno '{turno_guardado.Tipo_turno}' actualizado correctamente.")
            else:
                messages.success(request, "Nuevo Tipo de Turno creado con éxito.")
                
            return redirect('gestion_tipos_turno')
        
        else:
            messages.error(request, "Error al guardar el turno. Revise los campos.")

    else:
        form = TurnoForm(instance=turno_a_editar)
        
    turnos_existentes = Turno.objects.all().order_by('Hora_inicio')
    
    context = {
        'titulo': 'Gestión de Tipos de Turnos',
        'form': form,
        'turnos_existentes': turnos_existentes,
        'modo_edicion': id_turno is not None,
    }
    return render(request, 'turnos/gestion_tipos_turno.html', context)


@login_required
@permission_required('turnos.delete_turno', raise_exception=True)
def eliminar_tipo_turno(request, id_turno):
    
    turno = get_object_or_404(Turno, ID_turno=id_turno)
    
    if request.method == 'POST':
        turno.delete()
        messages.success(request, f"Tipo de turno '{turno.Tipo_turno}' eliminado correctamente.")
        return redirect('gestion_tipos_turno')
    
    return redirect('gestion_tipos_turno')

@login_required
def crear_solicitud_cambio(request):
    
    try:
        operador_persona = request.user.persona 
    except Persona.DoesNotExist:
        messages.error(request, "Error de perfil: No puedes solicitar un cambio sin un perfil de bombero asociado.")
        return redirect('mi_perfil')

    if request.method == 'POST':
        
        # 1. Obtenemos los turnos disponibles ANTES de validar el formulario (POST)
        turnos_disponibles = RegistroTurno.objects.filter(
            Rut=operador_persona,
            Fecha__gte=datetime.date.today()
        ).filter(
            ID_estado__Nombre_estado__in=['Normal', 'Atraso']
        ).order_by('Fecha')

        form = SolicitudCambioForm(request.POST)
        
        # 2. Asignamos la QuerySet al campo del formulario para la validación
        form.fields['registro_turno'].queryset = turnos_disponibles
        
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.persona_solicitante = operador_persona
            solicitud.save()
            messages.success(request, "Solicitud de cambio enviada. Estado: En Proceso.")
            return redirect('mi_perfil') 
        else:
            # Si falla, el mensaje de error "Revise los campos" ya se ha mostrado.
            messages.error(request, "Error al enviar la solicitud. Revise los campos.")
    
    else:
        # Método GET: Instanciamos el formulario y asignamos la QuerySet para mostrar.
        turnos_disponibles = RegistroTurno.objects.filter(
            Rut=operador_persona,
            Fecha__gte=datetime.date.today()
        ).filter(
            ID_estado__Nombre_estado__in=['Normal', 'Atraso']
        ).order_by('Fecha')
        
        form = SolicitudCambioForm()
        form.fields['registro_turno'].queryset = turnos_disponibles
    
    context = {
        'titulo': 'Solicitar Cambio de Turno',
        'form': form,
    }
    return render(request, 'turnos/crear_solicitud.html', context)


@login_required
@permission_required('turnos.view_solicitudcambio', raise_exception=True)
def gestionar_solicitudes(request):
    
    solicitudes_pendientes = SolicitudCambio.objects.filter(estado='Pendiente').order_by('fecha_solicitud')
    solicitudes_historicas = SolicitudCambio.objects.exclude(estado='Pendiente').order_by('-fecha_solicitud')
    
    context = {
        'titulo': 'Gestión de Solicitudes de Cambio',
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_historicas': solicitudes_historicas,
    }
    return render(request, 'turnos/gestionar_solicitudes.html', context)


@login_required
@permission_required('turnos.change_solicitudcambio', raise_exception=True)
def procesar_solicitud(request, id_solicitud, accion):
    
    solicitud = get_object_or_404(SolicitudCambio, id=id_solicitud)
    
    if solicitud.estado != 'Pendiente':
        messages.error(request, "Esta solicitud ya fue procesada.")
        return redirect('gestionar_solicitudes')

    if request.method == 'POST':
        solicitud.autorizado_por = request.user
        
        if accion == 'aceptar':
            
            registro_a_eliminar = solicitud.registro_turno
            
            try:
                registro_a_eliminar.delete() 
                
                solicitud.registro_turno = None 
                
                solicitud.estado = 'Aceptada'
                messages.success(request, f"Solicitud ACEPTADA. El turno programado ({registro_a_eliminar.ID_turno.Tipo_turno} del {registro_a_eliminar.Fecha}) ha sido ELIMINADO automáticamente.")
            
            except Exception as e:
                messages.error(request, f"Error fatal: No se pudo eliminar el turno o actualizar la solicitud. {e}")
                return redirect('gestionar_solicitudes')
            
        elif accion == 'rechazar':
            solicitud.estado = 'Rechazada'
            messages.warning(request, f"Solicitud de {solicitud.persona_solicitante.Apellido} RECHAZADA.")
            
        solicitud.save() 
        return redirect('gestionar_solicitudes')
    
    return redirect('gestionar_solicitudes')