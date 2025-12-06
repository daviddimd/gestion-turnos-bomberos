from django.db import models
from django.contrib.auth.models import User

class Area(models.Model):
    ID_area = models.AutoField(primary_key=True)
    Nombre_area = models.CharField(max_length=50)
    def __str__(self): return self.Nombre_area
    class Meta:
        db_table = 'area'
    
class Cargo(models.Model):
    ID_cargo = models.AutoField(primary_key=True)
    Nombre_cargo = models.CharField(max_length=50)
    def __str__(self): return self.Nombre_cargo
    class Meta:
        db_table = 'cargo'

class Turno(models.Model):
    ID_turno = models.AutoField(primary_key=True)
    Tipo_turno = models.CharField(max_length=50)
    Hora_inicio = models.TimeField()
    Hora_fin = models.TimeField()
    Duracion_horas = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    def __str__(self): return f"{self.Tipo_turno} ({self.Hora_inicio.strftime('%H:%M')} - {self.Hora_fin.strftime('%H:%M')})"
    class Meta:
        db_table = 'turnos_turno'

class Estado(models.Model):
    ID_estado = models.AutoField(primary_key=True)
    Nombre_estado = models.CharField(max_length=50)
    def __str__(self): return self.Nombre_estado
    class Meta:
        db_table = 'estado'

class Persona(models.Model):
    Rut = models.CharField(max_length=15, primary_key=True)
    Nombre = models.CharField(max_length=50)
    Apellido = models.CharField(max_length=50)
    Telefono = models.CharField(max_length=15, blank=True, null=True)
    Email = models.EmailField(unique=True, blank=True, null=True)
    Fecha_ingreso = models.DateField()
    ID_area = models.ForeignKey(Area, on_delete=models.PROTECT)
    ID_cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='persona', null=True)
    def __str__(self): return f"{self.Nombre} {self.Apellido} ({self.Rut})"
    class Meta:
        db_table = 'persona' 

class RegistroTurno(models.Model):
    ID_registro = models.AutoField(primary_key=True)
    Fecha = models.DateField()
    Hora_llegada_real = models.TimeField(blank=True, null=True)
    Minutos_tardanza = models.IntegerField(default=0)
    Rut = models.ForeignKey(Persona, on_delete=models.PROTECT, db_column='Rut_id')
    ID_turno = models.ForeignKey(Turno, on_delete=models.CASCADE, db_column='ID_turno_id')
    ID_estado = models.ForeignKey(Estado, on_delete=models.PROTECT, db_column='ID_estado_id')
    def __str__(self): return f"{self.Rut.Apellido} - {self.ID_turno.Tipo_turno} ({self.Fecha})"
    class Meta:
        db_table = 'registro_turno'
        unique_together = (('Rut', 'Fecha'),)

class SolicitudCambio(models.Model):
    ESTADOS_SOLICITUD = [('Pendiente', 'Pendiente'), ('Aceptada', 'Aceptada'), ('Rechazada', 'Rechazada')]
    persona_solicitante = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
    registro_turno = models.ForeignKey(RegistroTurno, on_delete=models.SET_NULL, null=True, related_name='solicitudes_de_cambio')
    razon = models.TextField(verbose_name="Razón de la solicitud")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADOS_SOLICITUD, default='Pendiente')
    autorizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_procesadas')
    def __str__(self): return f"Solicitud {self.id} de {self.persona_solicitante.Apellido}"
    class Meta:
        db_table = 'turnos_solicitudcambio'