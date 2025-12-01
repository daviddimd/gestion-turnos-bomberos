from django.shortcuts import render
from .models import Persona, Turno, RegistroTurno # Importamos los modelos

def inicio_gestion(request):
    """Muestra un resumen de las personas y los turnos."""
    
    # Usamos el ORM para obtener datos de la BDD
    personal = Persona.objects.all().order_by('Apellido')
    turnos_programados = Turno.objects.all()
    
    # Contamos la asistencia de un día específico (ejemplo, hoy)
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
    # Renderizamos la plantilla (que crearemos en el siguiente paso)
    return render(request, 'turnos/inicio.html', context)

# turnos/views.py (Añade esta función)

from django.shortcuts import render, get_object_or_404
from .models import Persona, Turno, RegistroTurno 
# Nota: get_object_or_404 es para buscar un objeto o mostrar un error 404 si no existe.
import datetime

# ... (código de inicio_gestion) ...

def detalle_personal(request, rut):
    """Muestra la información y el historial de turnos de una persona específica."""
    
    # Busca la persona por el RUT. Si no la encuentra, lanza un error 404.
    persona = get_object_or_404(Persona, Rut=rut)
    
    # Busca todos los registros de turnos asociados a ese RUT, ordenados por fecha descendente
    historial_turnos = RegistroTurno.objects.filter(Rut=persona).order_by('-Fecha')
    
    context = {
        'persona': persona,
        'historial_turnos': historial_turnos,
        'titulo': f'Historial de {persona.Nombre} {persona.Apellido}'
    }
    
    return render(request, 'turnos/detalle_personal.html', context)

from django.shortcuts import render, get_object_or_404
from .models import Persona, Turno, RegistroTurno
import datetime

# ... (código de inicio_gestion y detalle_personal) ...

def programacion_semanal(request):
    """Muestra la programación de turnos para la semana actual."""
    
    # 1. Calcular el rango de la semana actual (Lunes a Domingo)
    hoy = datetime.date.today()
    # weekday() devuelve 0 para lunes, 6 para domingo
    dia_inicio_semana = hoy - datetime.timedelta(days=hoy.weekday())
    dia_fin_semana = dia_inicio_semana + datetime.timedelta(days=6)
    
    rango_dias = [dia_inicio_semana + datetime.timedelta(days=i) for i in range(7)]

    # 2. Obtener todos los registros de turno para esa semana
    registros_semana = RegistroTurno.objects.filter(
        Fecha__gte=dia_inicio_semana,  # Mayor o igual que el día de inicio
        Fecha__lte=dia_fin_semana      # Menor o igual que el día de fin
    ).order_by('Fecha', 'ID_turno__Hora_inicio')

    # 3. Organizar los registros por día y por tipo de turno para la plantilla
    programacion_por_dia = {}
    for dia in rango_dias:
        # Filtra los registros para el día actual
        registros_del_dia = [r for r in registros_semana if r.Fecha == dia]
        
        # Agrupa por tipo de turno (ej. Operador Radial Día, Oficina)
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

# turnos/views.py (Añade esta función)

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q # Importamos Q para búsquedas complejas
from .models import Persona, Turno, RegistroTurno, Estado
import datetime
import pytz # Para manejar zonas horarias, necesario para datetime

# Define la zona horaria (ajusta a la zona de tu país si es diferente)
# América/Santiago es común en Chile, si estás en otra zona, ajústala
ZONA_HORARIA = pytz.timezone('America/Santiago') 

def registrar_asistencia(request):
    """Muestra el formulario y procesa el registro de asistencia."""
    
    context = {'mensaje': None, 'clase': ''}
    
    if request.method == 'POST':
        rut_ingresado = request.POST.get('rut').strip()
        
        try:
            # 1. Verificar si la persona existe
            persona = Persona.objects.get(Rut=rut_ingresado)
        except Persona.DoesNotExist:
            context['mensaje'] = "Error: El RUT ingresado no se encuentra en el registro de personal."
            context['clase'] = 'error'
            return render(request, 'turnos/registrar_asistencia.html', context)
        
        # 2. Buscar un turno programado para hoy (RegistroTurno)
        hoy = datetime.date.today()
        # Filtra por la persona y por la fecha de hoy
        registro = RegistroTurno.objects.filter(Rut=persona, Fecha=hoy).first()

        if not registro:
            context['mensaje'] = f"Error: No hay turno programado para {persona.Nombre} hoy ({hoy})."
            context['clase'] = 'error'
            return render(request, 'turnos/registrar_asistencia.html', context)
        
        # 3. Procesar la hora de llegada
        hora_actual = datetime.datetime.now(ZONA_HORARIA).time()
        
        # La hora de inicio programada (de la tabla Turno)
        hora_inicio_programada = registro.ID_turno.Hora_inicio
        
        # Comparamos la hora (tenemos que hacer la comparación de tiempo de forma segura)
        llegada = datetime.datetime.combine(hoy, hora_actual)
        programada = datetime.datetime.combine(hoy, hora_inicio_programada)
        diferencia = llegada - programada

        minutos_tardanza = 0
        estado_id = 1 # 1 es 'Normal'
        
        if diferencia > datetime.timedelta(minutes=0):
            # Hay tardanza
            minutos_tardanza = int(diferencia.total_seconds() / 60)
            
            if minutos_tardanza > 5: # Si se considera atraso después de 5 minutos
                 estado_id = 2 # 2 es 'Atraso'
            else:
                 estado_id = 1 # Menos de 5 minutos se considera 'Normal'

        # 4. Actualizar el registro
        registro.Hora_llegada_real = hora_actual
        registro.Minutos_tardanza = minutos_tardanza
        registro.ID_estado = Estado.objects.get(ID_estado=estado_id) # Obtenemos el objeto Estado
        registro.save()
        
        context['mensaje'] = f"✅ Asistencia registrada para {persona.Nombre} {persona.Apellido} ({registro.ID_turno.Tipo_turno}). Estado: {registro.ID_estado.Nombre_estado}."
        context['clase'] = 'exito'
        
        # Redirigir para limpiar el POST y evitar doble envío
        return render(request, 'turnos/registrar_asistencia.html', context)
    
    # Si es una petición GET, simplemente muestra el formulario
    return render(request, 'turnos/registrar_asistencia.html', context)