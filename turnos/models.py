from django.db import models
from django.contrib.auth.models import User

ESTADO_SOLICITUD = (
    ('Pendiente', 'En Proceso'),
    ('Aceptada', 'Aceptada'),
    ('Rechazada', 'Rechazada'),
)

class Area(models.Model):
    ID_area = models.AutoField(primary_key=True)
    Nombre_area = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Áreas"
        db_table = 'area'

    def __str__(self):
        return self.Nombre_area

class Cargo(models.Model):
    ID_cargo = models.AutoField(primary_key=True)
    Nombre_cargo = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Cargos"
        db_table = 'cargo'

    def __str__(self):
        return self.Nombre_cargo

class Estado(models.Model):
    ID_estado = models.AutoField(primary_key=True)
    Nombre_estado = models.CharField(max_length=100)

    class Meta:
        db_table = 'estado'

    def __str__(self):
        return self.Nombre_estado

class Turno(models.Model):
    ID_turno = models.AutoField(primary_key=True)
    Tipo_turno = models.CharField(max_length=100)
    Hora_inicio = models.TimeField()
    Hora_fin = models.TimeField()

    class Meta:
        verbose_name = "Tipo de Horario Fijo"
        verbose_name_plural = "Tipos de Horario Fijo"
        db_table = 'turno'

    def __str__(self):
        return self.Tipo_turno

class Persona(models.Model):
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Cuenta de Usuario (Login)", 
        null=True, blank=True
    ) 
    
    Rut = models.CharField(max_length=15, primary_key=True) 
    Nombre = models.CharField(max_length=100)
    Apellido = models.CharField(max_length=100)
    Telefono = models.CharField(max_length=20, null=True, blank=True)
    Email = models.EmailField(max_length=100, null=True, blank=True)
    
    ID_area = models.ForeignKey(
        'Area', 
        on_delete=models.CASCADE, 
        verbose_name="Área",
        db_column='ID_area'
    )
    
    ID_cargo = models.ForeignKey(
        'Cargo', 
        on_delete=models.CASCADE, 
        verbose_name="Cargo",
        db_column='ID_cargo'
    )
    
    class Meta:
        verbose_name = "Personal de Bomberos"
        verbose_name_plural = "Personal de Bomberos"
        db_table = 'persona'

    def __str__(self):
        return f"{self.Apellido}, {self.Nombre} ({self.Rut})"

class RegistroTurno(models.Model):
    ID_registro = models.AutoField(primary_key=True)
    Fecha = models.DateField()
    
    Rut = models.ForeignKey(
        'Persona', 
        on_delete=models.CASCADE, 
        verbose_name="Bombero",
        db_column='Rut'
    )
    
    ID_turno = models.ForeignKey(
        'Turno', 
        on_delete=models.CASCADE, 
        verbose_name="Turno Programado",
        db_column='ID_turno'
    )
    
    ID_estado = models.ForeignKey(
        'Estado', 
        on_delete=models.CASCADE, 
        verbose_name="Estado de Asistencia",
        db_column='ID_estado'
    )
    
    Hora_llegada_real = models.TimeField(null=True, blank=True)
    Minutos_tardanza = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Asistencia Programada"
        verbose_name_plural = "Asistencia Programada"
        db_table = 'registro_turno'
        
    def __str__(self):
        return f"{self.ID_turno.Tipo_turno} ({self.ID_turno.Hora_inicio.strftime('%H:%M')} - {self.ID_turno.Hora_fin.strftime('%H:%M')}) | {self.Fecha.strftime('%d/%m/%Y')} | {self.Rut.Nombre} {self.Rut.Apellido}"


class SolicitudCambio(models.Model):
    
    persona_solicitante = models.ForeignKey(
        'Persona', 
        on_delete=models.CASCADE, 
        verbose_name="Solicitante",
        db_column='Rut_Solicitante',
    )
    
    registro_turno = models.ForeignKey(
        'RegistroTurno', 
        on_delete=models.CASCADE, 
        verbose_name="Turno a Cambiar",
        help_text="Selecciona el turno programado que deseas modificar.",
    )
    
    razon = models.TextField(
        verbose_name="Razón de la Solicitud",
        help_text="Explica brevemente por qué necesitas el cambio de turno.",
    )
    
    estado = models.CharField(
        max_length=10, 
        choices=ESTADO_SOLICITUD, 
        default='Pendiente',
        verbose_name="Estado de la Solicitud",
    )
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    autorizado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        verbose_name="Autorizado por",
    )

    class Meta:
        verbose_name = "Flujo de Cambio"
        verbose_name_plural = "Flujo de Cambio de Turno"

    def __str__(self):
        return f"Solicitud de {self.persona_solicitante.Nombre} - {self.estado}"