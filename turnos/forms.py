from django import forms
from .models import Turno, Persona, RegistroTurno, SolicitudCambio
from datetime import timedelta, datetime, date
from django.forms.widgets import TimeInput, HiddenInput
from decimal import Decimal # 🛑 NUEVA IMPORTACIÓN

class ProgramacionMasivaForm(forms.Form):
    persona = forms.ModelChoiceField(queryset=Persona.objects.all().order_by('Apellido'), label="Persona a Programar")
    tipo_turno = forms.ModelChoiceField(queryset=Turno.objects.all().order_by('Tipo_turno'), label="Tipo de Turno")
    fecha_inicio = forms.DateField(label="Fecha de Inicio (YYYY-MM-DD)", widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_fin = forms.DateField(label="Fecha de Fin (YYYY-MM-DD)", widget=forms.DateInput(attrs={'type': 'date'}))

class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['Tipo_turno', 'Hora_inicio', 'Hora_fin', 'Duracion_horas'] 
        
        widgets = {
            'Hora_inicio': TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'Hora_fin': TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'Duracion_horas': HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('Hora_inicio')
        hora_fin = cleaned_data.get('Hora_fin')

        if hora_inicio and hora_fin:
            fecha_ficticia = date(1900, 1, 1)
            
            inicio_dt = datetime.combine(fecha_ficticia, hora_inicio)
            fin_dt = datetime.combine(fecha_ficticia, hora_fin)
            
            if fin_dt <= inicio_dt:
                fin_dt += timedelta(days=1)
            
            duracion_timedelta = fin_dt - inicio_dt
            
            duracion_horas = duracion_timedelta.total_seconds() / 3600
            
            # 🛑 SOLUCIÓN FINAL: Redondear y forzar la conversión a objeto Decimal
            valor_redondeado = round(duracion_horas, 2)
            cleaned_data['Duracion_horas'] = Decimal(str(valor_redondeado))
            
        return cleaned_data

class SolicitudCambioForm(forms.ModelForm):
    registro_turno = forms.ModelChoiceField(
        queryset=RegistroTurno.objects.none(),
        label="Turno a Cambiar"
    )
    class Meta:
        model = SolicitudCambio
        fields = ['registro_turno', 'razon']