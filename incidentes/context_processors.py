# ======================================================================
# CONTEXT PROCESSOR: atajos de navegación de la barra superior.
# ======================================================================
# Un "context processor" es una función que Django ejecuta en CADA
# renderizado de plantilla y cuyo resultado queda disponible en TODAS
# las plantillas (sin tener que pasarlo manualmente desde cada vista).
#
# Aquí definimos UNA sola lista de secciones. La barra superior muestra
# todas MENOS la sección en la que estás. Para agregar un nuevo atajo en
# el futuro, basta con añadir una entrada a SECCIONES.


# Cada sección: url_name (nombre en urls.py), etiqueta visible e icono.
SECCIONES = [
    {'url_name': 'lista',     'etiqueta': 'Notificaciones',     'icono': '📋'},
    {'url_name': 'crear',     'etiqueta': 'Crear notificación', 'icono': '➕'},
    {'url_name': 'boquillas', 'etiqueta': 'Boquillas',          'icono': '📢'},
]


def atajos_navegacion(request):
    # Nombre de la URL activa (por ejemplo 'boquillas', 'crear', 'lista').
    # resolver_match puede no existir en algunas respuestas (errores, etc.).
    actual = getattr(request, 'resolver_match', None)
    nombre_actual = actual.url_name if actual else None

    # En la pagina de inicio NO mostramos atajos (las tarjetas ya cumplen esa
    # funcion y evitamos duplicar la navegacion).
    if nombre_actual == 'inicio':
        return {'atajos_navegacion': []}

    # En el resto: todas las secciones excepto la actual.
    atajos = [s for s in SECCIONES if s['url_name'] != nombre_actual]

    return {'atajos_navegacion': atajos}
