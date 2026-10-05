# render() muestra una plantilla; redirect() manda al usuario a otra direccion.
# get_object_or_404 busca un registro y, si no existe, muestra error 404 (no encontrado).
from django.shortcuts import render, redirect, get_object_or_404
# timezone.now() nos da la fecha/hora actual con la zona horaria del proyecto.
from django.utils import timezone

# Importamos nuestros modelos y formularios.
from .models import Incidente, Area, Persona, AREAS_DISPONIBLES, Boquilla
from .forms import IncidenteForm, AvanceForm

# Lista simple de nombres de areas (para el desplegable de la interfaz).
NOMBRES_AREAS = [nombre for nombre, _ in AREAS_DISPONIBLES]


# Funcion auxiliar: toma un texto con nombres separados por comas
# y devuelve una lista limpia (sin espacios de sobra ni vacios).
# Ejemplo: "DBA, Comunicaciones ,  " -> ['DBA', 'Comunicaciones']
def separar_por_comas(texto):
    if not texto:
        return []
    partes = texto.split(',')            # partimos por cada coma
    limpias = [p.strip() for p in partes]  # quitamos espacios alrededor
    return [p for p in limpias if p]     # descartamos los vacios


# Vista de INICIO: muestra las tarjetas de navegacion.
def inicio(request):
    return render(request, 'incidentes/inicio.html')


# Vista de BOQUILLAS: mensajes informativos previos reutilizables.
# - GET: muestra el editor + el historial de boquillas guardadas.
# - POST accion="guardar": guarda una nueva boquilla en el historial.
# - POST accion="eliminar": borra una boquilla del historial.
def boquillas(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'guardar':
            texto = request.POST.get('texto', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            # Solo guardamos si el analista escribio algo.
            if texto:
                Boquilla.objects.create(nombre=nombre, texto=texto)
            return redirect('boquillas')

        if accion == 'eliminar':
            boquilla_id = request.POST.get('boquilla_id')
            if boquilla_id:
                Boquilla.objects.filter(id=boquilla_id).delete()
            return redirect('boquillas')

        if accion == 'renombrar':
            boquilla_id = request.POST.get('boquilla_id')
            nuevo_nombre = request.POST.get('nombre', '').strip()
            if boquilla_id:
                Boquilla.objects.filter(id=boquilla_id).update(nombre=nuevo_nombre)
            # Si la peticion es AJAX (fetch), respondemos JSON en vez de redirigir.
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({'ok': True, 'nombre': nuevo_nombre})
            return redirect('boquillas')

    historial = Boquilla.objects.all()
    return render(request, 'incidentes/boquillas.html', {
        'historial': historial,
    })


# Vista del DASHBOARD gerencial (por ahora una pantalla simple; se completa despues).
def dashboard(request):
    total = Incidente.objects.count()
    activos = Incidente.objects.exclude(estado='resuelto').count()
    resueltos = Incidente.objects.filter(estado='resuelto').count()
    return render(request, 'incidentes/dashboard.html', {
        'total': total,
        'activos': activos,
        'resueltos': resueltos,
    })


# Vista que muestra la lista de notificaciones como tarjetas, con filtro.
def lista_incidentes(request):
    # Leemos el filtro del desplegable desde la URL (?filtro=activos/cerrados/todos).
    # Si no viene, por defecto mostramos los activos.
    filtro = request.GET.get('filtro', 'activos')

    if filtro == 'cerrados':
        incidentes = Incidente.objects.filter(estado='resuelto')
    elif filtro == 'todos':
        # "resuelto_orden": 0 para los activos, 1 para los resueltos.
        # Asi ordenamos primero los activos (0) y despues los resueltos (1).
        from django.db.models import Case, When, IntegerField
        incidentes = Incidente.objects.annotate(
            resuelto_orden=Case(
                When(estado='resuelto', then=1),
                default=0,
                output_field=IntegerField(),
            )
        ).order_by('resuelto_orden', '-fecha_creacion')
    else:  # 'activos'
        incidentes = Incidente.objects.exclude(estado='resuelto')

    return render(request, 'incidentes/lista.html', {
        'incidentes': incidentes,
        'filtro': filtro,
    })


# Vista para CREAR un incidente nuevo.
def crear_incidente(request):
    # Cuando el usuario ENVIA el formulario, el navegador manda un POST.
    if request.method == 'POST':
        # Metemos los datos enviados dentro del formulario para validarlos.
        formulario = IncidenteForm(request.POST)
        if formulario.is_valid():
            # Guardamos el incidente en la base de datos (Supabase).
            incidente = formulario.save()

            # AREAS: viene como texto separado por comas (lo llena el JavaScript).
            texto_areas = formulario.cleaned_data.get('areas_seleccionadas', '')
            for nombre_area in separar_por_comas(texto_areas):
                Area.objects.create(incidente=incidente, nombre=nombre_area)

            # PERSONAS: viene como texto separado por comas; lo partimos.
            texto_personas = formulario.cleaned_data.get('personas_texto', '')
            for nombre_persona in separar_por_comas(texto_personas):
                Persona.objects.create(incidente=incidente, nombre=nombre_persona)

            # Mandamos al usuario al DETALLE del incidente recien creado.
            return redirect('detalle', incidente_id=incidente.id)
    else:
        # Si NO es POST (es la primera visita), mostramos un formulario vacio.
        formulario = IncidenteForm()

    # Mostramos la plantilla con el formulario (vacio o con errores).
    return render(request, 'incidentes/crear.html', {
        'formulario': formulario,
        'nombres_areas': NOMBRES_AREAS,
    })


# Funcion que arma el texto listo para WhatsApp de un incidente.
# solo_ultimo=True -> incluye solo el ultimo avance; False -> incluye todos.
def generar_texto_whatsapp(incidente, areas, personas, avances, solo_ultimo=False):
    # Encabezado segun el estado.
    if incidente.estado == 'resuelto':
        encabezado = '✅ *CIERRE DE INCIDENTE* ✅'
    else:
        encabezado = '⚠️ *INICIO DE INCIDENTE* ⚠️'

    # Formato de fecha/hora en 24h, convertido a la zona horaria del proyecto (Honduras).
    # timezone.localtime() convierte la hora guardada (UTC) a America/Tegucigalpa.
    def formato(fecha):
        if not fecha:
            return '—'
        return timezone.localtime(fecha).strftime('%d/%m/%Y %H:%M')

    # Construimos el texto linea por linea. \n significa "salto de linea".
    lineas = []
    lineas.append(encabezado)
    lineas.append('')
    # Etiquetas entre asteriscos (*texto*) para que WhatsApp las muestre en NEGRITA.
    # Linea unificada: "Incidente: TICKET - Nombre".
    ticket_txt = incidente.ticket or "Por generarse"
    lineas.append(f'📌 *Incidente:* {ticket_txt} - {incidente.incidente}')
    lineas.append(f'👥 *Afectación a cliente:* {incidente.get_afectacion_cliente_display()}')
    lineas.append(f'🔺 *Prioridad:* {incidente.prioridad}')
    lineas.append(f'🔍 *¿Cómo se detectó?:* {incidente.get_como_se_detecto_display() or "—"}')
    lineas.append('')
    lineas.append(f'🕐 *Hora inicio de falla:* {formato(incidente.hora_inicio)}')
    if incidente.estado == 'resuelto':
        lineas.append(f'🕐 *Hora fin de falla:* {formato(incidente.fecha_cierre)}')
    lineas.append(f'📌 *Estado:* {incidente.get_estado_display()}')
    lineas.append('')
    lineas.append(f'📝 *Descripción:* {incidente.descripcion or "—"}')
    lineas.append('')

    # Areas involucradas.
    lineas.append('*Áreas involucradas:*')
    for area in areas:
        lineas.append(f'- {area.nombre}')
    lineas.append('')

    # Personas involucradas.
    lineas.append('*Personas involucradas:*')
    for persona in personas:
        lineas.append(f'- {persona.nombre}')
    lineas.append('')

    # Avances: todos, o solo el ultimo, segun la opcion elegida.
    # Solo mostramos la seccion "Avances" si realmente hay avances
    # (en la primera notificacion no lleva avances, por eso no aparece).
    lista_avances = list(avances)
    if solo_ultimo and lista_avances:
        lista_avances = [lista_avances[-1]]  # solo el ultimo
    if lista_avances:
        lineas.append('*Avances*')
        for avance in lista_avances:
            lineas.append(f'- 🕐 {formato(avance.hora)}: {avance.texto}')
        lineas.append('')

    # Solucion (solo si esta resuelto). Incluimos el estado "Resuelto".
    if incidente.estado == 'resuelto':
        # Si la ultima linea no quedo vacia, agregamos un separador.
        if lineas and lineas[-1] != '':
            lineas.append('')
        lineas.append('✅ *Solución (Resuelto):*')
        lineas.append(incidente.solucion or '—')

    # Unimos todas las lineas con saltos de linea.
    return '\n'.join(lineas)


# Auxiliar: crea el IncidenteForm precargado con los datos del incidente,
# incluyendo las areas (casillas) y personas (texto con comas) actuales.
def _form_incidente_precargado(incidente):
    areas_actuales = ', '.join(incidente.areas.values_list('nombre', flat=True))
    personas_actuales = ', '.join(incidente.personas.values_list('nombre', flat=True))
    # Convertimos la hora guardada (UTC) a hora local de Honduras para que
    # el input datetime-local muestre la hora correcta con la que se creo.
    hora_local = timezone.localtime(incidente.hora_inicio) if incidente.hora_inicio else None
    return IncidenteForm(instance=incidente, initial={
        'areas_seleccionadas': areas_actuales,
        'personas_texto': personas_actuales,
        'hora_inicio': hora_local,
    })


# Vista de DETALLE / VER (Opcion A): formulario editable + avances + WhatsApp.
def detalle_incidente(request, incidente_id):
    incidente = get_object_or_404(Incidente, id=incidente_id)

    if request.method == 'POST':
        # Distinguimos que formulario se envio con un campo oculto "accion".
        accion = request.POST.get('accion')

        if accion == 'guardar_datos':
            # Guardamos la solucion actual para no perderla (no viene en este form).
            solucion_actual = incidente.solucion
            # Editar los datos base del incidente (formulario precargado).
            formulario = IncidenteForm(request.POST, instance=incidente)
            if formulario.is_valid():
                inc = formulario.save(commit=False)
                inc.solucion = solucion_actual  # preservamos la solucion
                inc.save()
                # Reemplazamos las areas: borramos las actuales y ponemos las elegidas.
                incidente.areas.all().delete()
                for nombre_area in separar_por_comas(formulario.cleaned_data.get('areas_seleccionadas', '')):
                    Area.objects.create(incidente=incidente, nombre=nombre_area)
                # Reemplazamos las personas.
                incidente.personas.all().delete()
                for nombre_persona in separar_por_comas(formulario.cleaned_data.get('personas_texto', '')):
                    Persona.objects.create(incidente=incidente, nombre=nombre_persona)
                return redirect('detalle', incidente_id=incidente.id)
            formulario_avance = AvanceForm()

        elif accion == 'agregar_avance':
            # Agregar un avance nuevo.
            formulario = _form_incidente_precargado(incidente)
            formulario_avance = AvanceForm(request.POST)
            if formulario_avance.is_valid():
                nuevo_avance = formulario_avance.save(commit=False)
                nuevo_avance.incidente = incidente
                nuevo_avance.save()
                return redirect('detalle', incidente_id=incidente.id)

        elif accion == 'guardar_solucion':
            # Guardar solo el campo de solucion.
            incidente.solucion = request.POST.get('solucion', '').strip()
            incidente.save()
            return redirect('detalle', incidente_id=incidente.id)
        else:
            formulario = _form_incidente_precargado(incidente)
            formulario_avance = AvanceForm()
    else:
        # Primera visita: mostramos el formulario PRECARGADO con los datos actuales.
        formulario = _form_incidente_precargado(incidente)
        formulario_avance = AvanceForm()

    avances = incidente.avances.all()
    areas = incidente.areas.all()
    personas = incidente.personas.all()

    # Generamos DOS versiones del texto de WhatsApp:
    #   - con todos los avances
    #   - con solo el ultimo avance
    texto_todos = generar_texto_whatsapp(incidente, areas, personas, avances, solo_ultimo=False)
    texto_ultimo = generar_texto_whatsapp(incidente, areas, personas, avances, solo_ultimo=True)

    return render(request, 'incidentes/detalle.html', {
        'incidente': incidente,
        'formulario': formulario,
        'nombres_areas': NOMBRES_AREAS,
        'avances': avances,
        'areas': areas,
        'personas': personas,
        'formulario_avance': formulario_avance,
        'texto_todos': texto_todos,
        'texto_ultimo': texto_ultimo,
    })


# Vista "GENERAR ACTUALIZACION": agrega un avance nuevo al incidente.
def actualizar_incidente(request, incidente_id):
    incidente = get_object_or_404(Incidente, id=incidente_id)

    if request.method == 'POST':
        formulario_avance = AvanceForm(request.POST)
        if formulario_avance.is_valid():
            texto_avance = formulario_avance.cleaned_data.get('texto')
            # El avance es opcional aqui: solo lo guardamos si escribieron algo.
            if texto_avance:
                nuevo_avance = formulario_avance.save(commit=False)
                nuevo_avance.incidente = incidente
                nuevo_avance.save()
            # Tras guardar, volvemos al listado de notificaciones.
            return redirect('lista')
    else:
        formulario_avance = AvanceForm()
        formulario_avance.fields['texto'].required = False

    # Hora de inicio en texto (24h) para la vista previa.
    hora_inicio_txt = incidente.hora_inicio.strftime('%d/%m/%Y %H:%M') if incidente.hora_inicio else '—'

    # Reutilizamos una misma plantilla para actualizar y resolver,
    # cambiando el titulo y el modo con estas variables.
    return render(request, 'incidentes/actualizar.html', {
        'incidente': incidente,
        'formulario_avance': formulario_avance,
        'titulo': 'Actualización Incidente',
        'modo': 'actualizar',
        'hora_inicio_txt': hora_inicio_txt,
        'permite_editar_ticket': True,
    })


# Vista "RESOLVER": cierra el incidente (estado = resuelto + fecha de cierre).
# Al resolver NO se pide avance; solo la solucion.
def resolver_incidente(request, incidente_id):
    incidente = get_object_or_404(Incidente, id=incidente_id)

    if request.method == 'POST':
        # Tomamos la solucion escrita en el formulario.
        solucion = request.POST.get('solucion', '').strip()
        if solucion:
            incidente.solucion = solucion

        # Cambiamos el estado a resuelto y registramos la hora de cierre.
        incidente.estado = 'resuelto'
        incidente.fecha_cierre = timezone.now()
        incidente.save()

        return redirect('lista')

    hora_inicio_txt = incidente.hora_inicio.strftime('%d/%m/%Y %H:%M') if incidente.hora_inicio else '—'

    return render(request, 'incidentes/actualizar.html', {
        'incidente': incidente,
        'titulo': 'Incidente Resuelto',
        'modo': 'resolver',
        'hora_inicio_txt': hora_inicio_txt,
    })
