# Importamos las herramientas de Django para crear modelos (tablas de datos).
from django.db import models


# Lista fija de areas de la empresa (misma del proyecto de Honduras).
# Se usa para mostrar las casillas de "Areas involucradas".
# Cada par es ('valor_guardado', 'texto_visible'); aqui usamos el mismo texto para ambos.
AREAS_DISPONIBLES = [
    ('Aplicaciones', 'Aplicaciones'),
    ('AS400', 'AS400'),
    ('ATM/Data Center', 'ATM/Data Center'),
    ('Basis', 'Basis'),
    ('Comunicaciones', 'Comunicaciones'),
    ('Control M', 'Control M'),
    ('DBA', 'DBA'),
    ('Desarrollo', 'Desarrollo'),
    ('Incidentes', 'Incidentes'),
    ('Medios Electrónicos', 'Medios Electrónicos'),
    ('Monitoreo', 'Monitoreo'),
    ('Mesa de Servicio 1', 'Mesa de Servicio 1'),
    ('Mesa de Servicio 2', 'Mesa de Servicio 2'),
    ('Observabilidad', 'Observabilidad'),
    ('PO', 'PO'),
    ('Procesadora', 'Procesadora'),
    ('ATM REN Procesadora', 'ATM REN Procesadora'),
    ('Seguridad Informática', 'Seguridad Informática'),
    ('Servicios TI', 'Servicios TI'),
    ('Servidores', 'Servidores'),
    ('SMO', 'SMO'),
    ('Soporte Técnico', 'Soporte Técnico'),
    ('Soporte N1', 'Soporte N1'),
]


# Un "modelo" es una clase de Python que representa una TABLA en la base de datos.
# Cada atributo (variable) dentro de la clase es una COLUMNA de esa tabla.
# Django se encarga de traducir esto a la base de datos por nosotros.
class Incidente(models.Model):

    # ------------------------------------------------------------------
    # OPCIONES FIJAS
    # ------------------------------------------------------------------
    # Estas listas definen los únicos valores permitidos para ciertos campos.
    # Cada opción es un par: ('valor_guardado', 'texto_que_ve_el_usuario').

    PRIORIDADES = [
        ('P1', 'P1 - Crítica'),
        ('P2', 'P2 - Alta'),
        ('P3', 'P3 - Media'),
        ('P4', 'P4 - Baja'),
    ]

    ESTADOS = [
        ('abierto', 'Abierto'),
        ('en_gestion', 'En gestión'),
        ('resuelto', 'Resuelto'),
    ]

    AFECTACION = [
        ('Si', 'Sí'),
        ('No', 'No'),
    ]

    # Opciones para el desplegable "¿Cómo se detectó?".
    FORMA_DETECCION = [
        ('Monitoreo', 'Monitoreo'),
        ('Usuario Final', 'Usuario Final'),
        ('Proveedor', 'Proveedor'),
        ('Otro', 'Otro'),
    ]

    # ------------------------------------------------------------------
    # CAMPOS (columnas de la tabla)
    # ------------------------------------------------------------------

    # Texto corto (una línea). max_length = largo máximo de caracteres.
    incidente = models.CharField('Nombre del incidente', max_length=200)

    # blank=True  -> se permite dejarlo vacío en los formularios.
    # null=True   -> se permite guardar "nada" en la base de datos.
    # unique=True: no se permite repetir ticket. null=True + blank=True permiten
    # que varios incidentes queden SIN ticket (varios NULL si estan permitidos).
    ticket = models.CharField('Ticket generado', max_length=100, blank=True, null=True, unique=True)

    # Campo con opciones fijas: usa la lista PRIORIDADES definida arriba.
    # default = valor que toma si no se elige otro.
    prioridad = models.CharField('Prioridad', max_length=2, choices=PRIORIDADES, default='P3')

    estado = models.CharField('Estado', max_length=20, choices=ESTADOS, default='abierto')

    afectacion_cliente = models.CharField('Afectación a cliente', max_length=2, choices=AFECTACION, default='No')

    # Desplegable: solo permite una de las 4 opciones de FORMA_DETECCION.
    como_se_detecto = models.CharField('¿Cómo se detectó?', max_length=20, choices=FORMA_DETECCION, blank=True, null=True)

    # Texto libre para el detalle (antes se llamaba "Reporte inicial").
    reporte_inicial = models.CharField('Cómo se detectó el incidente', max_length=200, blank=True, null=True)

    asignado_a = models.CharField('Asignado a', max_length=200, blank=True, null=True)

    # Texto largo (varias líneas), para descripciones extensas.
    descripcion = models.TextField('Descripción', blank=True, null=True)

    solucion = models.TextField('Solución', blank=True, null=True)

    # Fecha y hora en que empezó la falla. Puede quedar vacía.
    hora_inicio = models.DateTimeField('Hora inicio de falla', blank=True, null=True)

    # Fecha y hora de cierre. Se llenará cuando el incidente se resuelva.
    fecha_cierre = models.DateTimeField('Fecha de cierre', blank=True, null=True)

    # auto_now_add=True -> Django pone la fecha/hora AUTOMÁTICAMENTE al crear el registro.
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)

    # ------------------------------------------------------------------
    # CONFIGURACIÓN Y REPRESENTACIÓN
    # ------------------------------------------------------------------

    class Meta:
        # Ordena los incidentes del más nuevo al más viejo por defecto.
        # El signo "-" significa orden descendente.
        ordering = ['-fecha_creacion']
        verbose_name = 'Incidente'
        verbose_name_plural = 'Incidentes'

    # __str__ define cómo se "ve" un incidente cuando se muestra como texto
    # (por ejemplo, en el panel de administración). Devolvemos algo legible.
    def __str__(self):
        return f'#{self.id} - {self.incidente}'


# ======================================================================
# MODELO AVANCE (tabla separada, relacionada con Incidente)
# ======================================================================
# Un incidente puede tener MUCHOS avances a lo largo del tiempo.
# Por eso los avances viven en su PROPIA tabla, conectada al incidente.
# Esto se llama relacion "uno a muchos": 1 Incidente -> muchos Avances.
class Avance(models.Model):

    # ForeignKey = el "hilo" que conecta cada avance con su incidente.
    #   - Incidente: a que modelo se conecta.
    #   - on_delete=models.CASCADE: si se borra el incidente, se borran sus avances.
    #   - related_name='avances': nos permite escribir incidente.avances.all()
    #     para obtener todos los avances de un incidente.
    incidente = models.ForeignKey(
        Incidente,
        on_delete=models.CASCADE,
        related_name='avances'
    )

    # El texto del avance (varias lineas).
    texto = models.TextField('Descripción del avance')

    # La fecha y hora del avance. auto_now_add=True -> se pone sola al crear.
    hora = models.DateTimeField('Hora del avance', auto_now_add=True)

    class Meta:
        # Ordenamos los avances del mas viejo al mas nuevo (orden cronologico).
        ordering = ['hora']
        verbose_name = 'Avance'
        verbose_name_plural = 'Avances'

    def __str__(self):
        return f'Avance de #{self.incidente_id} - {self.hora}'


# ======================================================================
# MODELO AREA (areas involucradas en el incidente)
# ======================================================================
# Un incidente puede involucrar MUCHAS areas -> relacion uno a muchos.
class Area(models.Model):

    incidente = models.ForeignKey(
        Incidente,
        on_delete=models.CASCADE,
        related_name='areas'  # permite incidente.areas.all()
    )

    nombre = models.CharField('Nombre del área', max_length=100)

    class Meta:
        verbose_name = 'Área involucrada'
        verbose_name_plural = 'Áreas involucradas'

    def __str__(self):
        return self.nombre


# ======================================================================
# MODELO PERSONA (personas involucradas en el incidente)
# ======================================================================
# Un incidente puede involucrar MUCHAS personas -> relacion uno a muchos.
class Persona(models.Model):

    incidente = models.ForeignKey(
        Incidente,
        on_delete=models.CASCADE,
        related_name='personas'  # permite incidente.personas.all()
    )

    nombre = models.CharField('Nombre de la persona', max_length=150)

    class Meta:
        verbose_name = 'Persona involucrada'
        verbose_name_plural = 'Personas involucradas'

    def __str__(self):
        return self.nombre


# ======================================================================
# MODELO BOQUILLA (mensajes informativos previos reutilizables)
# ======================================================================
# Una "boquilla" es un mensaje informativo corto que el analista escribe
# y que va enmarcado entre los banners "📢 Nos permitimos informar que: 📢".
# Se guardan a criterio del analista para ir creando un HISTORIAL de uso,
# de modo que despues solo haya que copiarlas desde el frente con un boton.
class Boquilla(models.Model):

    # Nombre corto para identificar la boquilla en el historial.
    nombre = models.CharField('Nombre de la boquilla', max_length=120, blank=True, default='')

    # El texto que escribe el analista (varias lineas).
    texto = models.TextField('Mensaje de la boquilla')

    # Fecha y hora en que se guardo (se pone sola al crear).
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)

    class Meta:
        # Mostramos primero las mas recientes.
        ordering = ['-fecha_creacion']
        verbose_name = 'Boquilla'
        verbose_name_plural = 'Boquillas'

    def __str__(self):
        # Si tiene nombre, lo usamos; si no, un resumen del texto.
        if self.nombre:
            return f'Boquilla #{self.id} - {self.nombre}'
        resumen = (self.texto or '').strip().replace('\n', ' ')
        if len(resumen) > 50:
            resumen = resumen[:50] + '…'
        return f'Boquilla #{self.id} - {resumen}'
