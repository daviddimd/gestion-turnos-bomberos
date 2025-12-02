from django import forms
from .models import Persona, Turno

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