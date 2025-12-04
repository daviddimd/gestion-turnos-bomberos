from django import forms
from .models import Persona, Turno ,SolicitudCambio

class ProgramacionMasivaForm(forms.Form):
    """Formulario para asignar un turno a una persona durante un rango de fechas."""

    persona = forms.ModelChoiceField(
        queryset=Persona.objects.all().order_by('Apellido'),
        label="Seleccionar Personal",
        required=True
    )

    tipo_turno = forms.ModelChoiceField(
        queryset=Turno.objects.all().order_by('Tipo_turno'),
        label="Tipo de Turno a Asignar",
        required=True
    )

    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Fecha de Inicio"
    )

    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Fecha de Fin"
    )

class TurnoForm(forms.ModelForm):
    """Formulario para crear o editar un Tipo de Turno."""
    
    class Meta:
        model = Turno
        fields = ['Tipo_turno', 'Hora_inicio', 'Hora_fin'] 
        widgets = {
            'Hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'Hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }

class SolicitudCambioForm(forms.ModelForm):
    """Formulario para que un empleado solicite un cambio de turno."""
    
    class Meta:
        model = SolicitudCambio
        fields = ['registro_turno', 'razon']
        widgets = {
            'razon': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Explica brevemente la razón del cambio.'}),
        }