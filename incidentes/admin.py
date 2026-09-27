# Importamos el módulo de administración de Django.
from django.contrib import admin

# Importamos nuestros modelos para poder registrarlos.
from .models import Incidente, Avance, Area, Persona, Boquilla


# Un "inline" permite editar registros relacionados DENTRO de la ficha del incidente,
# en la misma pantalla, en lugar de una tabla separada.
class AvanceInline(admin.TabularInline):
    model = Avance
    extra = 1  # cuantas filas vacias mostrar para agregar nuevos.


class AreaInline(admin.TabularInline):
    model = Area
    extra = 1


class PersonaInline(admin.TabularInline):
    model = Persona
    extra = 1


# El decorador @admin.register(Incidente) le dice al panel de administración:
# "muestra y administra el modelo Incidente".
# La clase de abajo personaliza CÓMO se ve ese modelo dentro del panel.
@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):

    # list_display: qué columnas se muestran en la lista de incidentes.
    list_display = ('id', 'incidente', 'ticket', 'prioridad', 'estado', 'fecha_creacion')

    # list_filter: agrega filtros laterales para buscar por estos campos.
    list_filter = ('estado', 'prioridad', 'afectacion_cliente')

    # search_fields: agrega una barra de búsqueda que busca en estos campos.
    search_fields = ('incidente', 'ticket', 'asignado_a')

    # inlines: muestra areas, personas y avances dentro de la ficha del incidente.
    inlines = [AreaInline, PersonaInline, AvanceInline]




# Registro del historial de boquillas en el panel de administracion.
@admin.register(Boquilla)
class BoquillaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'fecha_creacion')
    search_fields = ('nombre', 'texto')
