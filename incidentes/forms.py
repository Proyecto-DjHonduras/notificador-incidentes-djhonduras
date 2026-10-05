# forms es el modulo de Django para crear formularios.
from django import forms

# Importamos los modelos y la lista de areas para construir los formularios.
from .models import Incidente, Avance, AREAS_DISPONIBLES


# Un ModelForm es un formulario que se genera AUTOMATICAMENTE desde un modelo.
# Django crea los campos HTML (inputs, desplegables) mirando el modelo.
class IncidenteForm(forms.ModelForm):

    # AREAS: campo de texto OCULTO que guarda las areas elegidas separadas por comas.
    # La interfaz visual (input + desplegable + etiquetas) se maneja con JavaScript
    # en la plantilla, y va llenando este campo oculto.
    areas_seleccionadas = forms.CharField(
        label='Áreas involucradas',
        required=False,
        widget=forms.HiddenInput
    )

    # PERSONAS: se quedan como texto libre separado por comas.
    personas_texto = forms.CharField(
        label='Personas involucradas',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Juan Pérez, María López (separadas por comas)'})
    )

    # Si el ticket viene vacio, lo convertimos a None (NULL en la BD) para que
    # varios incidentes puedan quedar SIN ticket sin chocar con la regla de unicidad.
    # Ademas validamos que el ticket no este repetido y mostramos un mensaje claro.
    def clean_ticket(self):
        ticket = self.cleaned_data.get('ticket')
        if ticket:
            ticket = ticket.strip()
        # Si quedo vacio, lo tratamos como "sin ticket" (NULL) y no validamos duplicado.
        if not ticket:
            return None

        # Buscamos si ya existe otro incidente con ese mismo ticket.
        existentes = Incidente.objects.filter(ticket=ticket)
        # Si estamos EDITANDO, excluimos el propio incidente de la busqueda.
        if self.instance and self.instance.pk:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise forms.ValidationError(
                f'El ticket "{ticket}" ya existe. Usa un número de ticket diferente.'
            )

        return ticket

    class Meta:
        # A partir de que modelo se construye el formulario.
        model = Incidente

        # Que campos del modelo queremos mostrar en el formulario, y en que orden.
        # (Dejamos fuera fecha_creacion y fecha_cierre porque se manejan solos.)
        fields = [
            'incidente',
            'ticket',
            'prioridad',
            'estado',
            'afectacion_cliente',
            'como_se_detecto',
            'asignado_a',
            'hora_inicio',
            'descripcion',
            'solucion',
        ]

        # widgets nos deja personalizar como se ve cada campo en el HTML.
        widgets = {
            # Selector unico de fecha y hora del navegador (un solo control).
            # lang='es-HN' y step=60 sugieren 24h y minutos exactos.
            'hora_inicio': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'lang': 'es-HN',
                'step': 60,
            }),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'solucion': forms.Textarea(attrs={'rows': 3}),
        }


# Formulario pequeno para agregar UN avance a un incidente.
# Solo pedimos el texto; la hora se pone sola (auto_now_add en el modelo).
class AvanceForm(forms.ModelForm):

    class Meta:
        model = Avance
        fields = ['texto']
        # labels cambia el texto de la etiqueta que se ve en el formulario.
        labels = {
            'texto': 'Registrar Avance',
        }
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Describe el avance...'}),
        }
