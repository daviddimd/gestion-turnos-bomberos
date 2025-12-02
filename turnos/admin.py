# turnos/admin.py (Código completo y corregido con registro de Persona)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Area, Cargo, Estado, Persona, Turno, RegistroTurno

# 1. Definir la clase Inline para Persona (sin cambios)
class PersonaInline(admin.StackedInline):
    """Permite vincular o crear el perfil Persona dentro de la página del Usuario."""
    model = Persona
    max_num = 0 
    min_num = 0 
    can_delete = False 
    verbose_name_plural = 'Datos del Bombero (Perfil Persona)'
    fields = ('Rut', 'Nombre', 'Apellido', 'Telefono', 'Email', 'ID_area', 'ID_cargo')
    
# 2. Definir la nueva clase de Administración para el Usuario (User) (sin cambios)
class UserAdmin(BaseUserAdmin):
    """Personaliza la interfaz de Usuario (auth_user) añadiendo el perfil Persona."""
    inlines = (PersonaInline,)
    
# 3. Registrar TODOS los modelos de tu aplicación
admin.site.register(Area)
admin.site.register(Cargo)
admin.site.register(Estado)
admin.site.register(Turno)
admin.site.register(RegistroTurno)
admin.site.register(Persona)  # <-- ¡ESTA ES LA LÍNEA QUE FALTABA!

# 4. Desregistrar y registrar el modelo User (sin cambios)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)