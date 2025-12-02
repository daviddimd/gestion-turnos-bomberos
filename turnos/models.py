from django.db import models

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
        verbose_name_plural = "Estados"
        db_table = 'estado' 

    def __str__(self):
        return self.Nombre_estado

class Turno(models.Model):
    ID_turno = models.AutoField(primary_key=True)
    Tipo_turno = models.CharField(max_length=100)
    Hora_inicio = models.TimeField()
    Hora_fin = models.TimeField()

    class Meta:
        db_table = 'turno'

    def __str__(self):
        return self.Tipo_turno


class Persona(models.Model):
    # Rut es la clave primaria
    Rut = models.CharField(max_length=15, primary_key=True) 
    Nombre = models.CharField(max_length=100)
    Apellido = models.CharField(max_length=100)
    Telefono = models.CharField(max_length=20, null=True, blank=True)
    Email = models.EmailField(max_length=100, null=True, blank=True)
    
    ID_area = models.ForeignKey(
        Area, 
        on_delete=models.CASCADE, 
        verbose_name="Área",
        db_column='ID_area' 
    )
    
    ID_cargo = models.ForeignKey(
        Cargo, 
        on_delete=models.CASCADE, 
        verbose_name="Cargo",
        db_column='ID_cargo'
    )
    
    class Meta:
        verbose_name_plural = "Personas"
        db_table = 'persona'

    def __str__(self):
        return f"{self.Nombre} {self.Apellido} ({self.Rut})"

class RegistroTurno(models.Model):
    ID_registro = models.AutoField(primary_key=True)
    Fecha = models.DateField()
    
    Rut = models.ForeignKey(
        Persona, 
        on_delete=models.CASCADE, 
        verbose_name="Bombero",
        db_column='Rut'
    )
    
    ID_turno = models.ForeignKey(
        Turno, 
        on_delete=models.CASCADE, 
        verbose_name="Turno Programado",
        db_column='ID_turno'
    )
    
    ID_estado = models.ForeignKey(
        Estado, 
        on_delete=models.CASCADE, 
        verbose_name="Estado de Asistencia",
        db_column='ID_estado'
    )
    
    Hora_llegada_real = models.TimeField(null=True, blank=True)
    Minutos_tardanza = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Registros de Turnos"
        db_table = 'registro_turno'
        
    def __str__(self):
        return f"Registro {self.Fecha} - {self.Rut.Apellido}"