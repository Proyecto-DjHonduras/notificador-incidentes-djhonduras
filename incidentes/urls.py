# path() sirve para definir una direccion web y decir que vista la atiende.
from django.urls import path

# Importamos las vistas de esta misma app.
from . import views

# urlpatterns es la lista de direcciones de ESTA app.
urlpatterns = [
    # Direccion vacia ('') = la pagina de INICIO (las tres tarjetas).
    path('', views.inicio, name='inicio'),

    # Listado de notificaciones (activas + historial).
    path('notificaciones/', views.lista_incidentes, name='lista'),

    # Dashboard gerencial.
    path('dashboard/', views.dashboard, name='dashboard'),

    # Boquillas: mensajes informativos previos reutilizables.
    path('boquillas/', views.boquillas, name='boquillas'),

    # Direccion 'nuevo/' = el formulario para crear un incidente.
    path('nuevo/', views.crear_incidente, name='crear'),

    # Direccion con un numero variable: '<int:incidente_id>/'.
    # Por ejemplo /1/ o /2/. Ese numero se le pasa a la vista detalle_incidente.
    # <int:...> significa "aqui va un numero entero".
    path('<int:incidente_id>/', views.detalle_incidente, name='detalle'),

    # Generar actualizacion (agregar avance) de un incidente.
    path('<int:incidente_id>/actualizar/', views.actualizar_incidente, name='actualizar'),

    # Resolver (cerrar) un incidente.
    path('<int:incidente_id>/resolver/', views.resolver_incidente, name='resolver'),
]
