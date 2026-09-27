# Guía del Proyecto: Notificador de Incidentes (Django + Supabase + Terraform)

Este documento es nuestro "cuaderno de bitácora". Anota, paso a paso y en lenguaje
sencillo, todo lo que hemos construido. Está pensado para alguien que empieza desde
cero en programación.

---

## ¿Qué estamos construyendo?

Una aplicación web para registrar y notificar incidentes (similar al notificador de
Honduras original), con estas tecnologías:

- **Python**: el lenguaje de programación.
- **Django**: framework web de Python (nos da base de datos, formularios, seguridad).
- **Supabase**: base de datos PostgreSQL en la nube donde se guardan los datos.
- **Terraform**: herramienta para desplegar la infraestructura (fase final, pendiente).

---

## Glosario rápido

- **Terminal / PowerShell**: ventana donde se escriben comandos.
- **pip**: instalador de paquetes de Python.
- **Entorno virtual (venv)**: "caja" aislada con las librerías del proyecto.
- **Framework**: kit de herramientas grande y organizado (Django).
- **Modelo**: definición de una tabla de datos (en models.py).
- **Vista (view)**: función que responde a una página (en views.py).
- **Plantilla (template)**: archivo HTML que ve el usuario.
- **Migración**: instrucción que crea/cambia tablas en la base de datos.

---

## CONCEPTOS CLAVE (para no perderse)

1. TERMINAL vs CÓDIGO:
   - La terminal (PowerShell) solo entiende COMANDOS (python manage.py..., pip...).
   - El código Python va DENTRO de archivos .py; NUNCA se pega en la terminal.
   - Kiro edita los archivos; el usuario ejecuta los comandos.
   - Al copiar un comando, copiar SOLO el comando, nunca el "PS C:\...>".

2. SIEMPRE activar el entorno virtual antes de instalar o ejecutar:
   ```
   .\venv\Scripts\Activate.ps1
   ```
   Debe verse "(venv)" al inicio de la línea.

3. En las PLANTILLAS de Django NO escribir {% %} ni {{ }} como ejemplo/adorno
   (ni en comentarios): Django intenta ejecutarlos y da error.

4. Cada vez que se cambia models.py hay que aplicar:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Cómo se arma una página (3 piezas):
   urls.py (direccion) -> views.py (logica) -> templates (lo que se ve).

---

## MAPA DEL PROYECTO (estructura actual)

```
notificador_DjHonduras\            <- CARPETA RAIZ
│
├── venv\                          <- Entorno virtual (no se toca, no se sube).
│
├── config\                        <- CONFIGURACION del proyecto.
│   ├── settings.py                   Ajustes: BD Supabase, apps, idioma, hora 24h, static.
│   ├── urls.py                       Mapa principal (enchufa la app incidentes).
│   ├── wsgi.py / asgi.py             Para el despliegue (fase final).
│   └── __init__.py
│
├── incidentes\                    <- NUESTRA APP.
│   ├── models.py                     Tablas: Incidente, Avance, Area, Persona + lista AREAS.
│   ├── forms.py                      Formularios: IncidenteForm, AvanceForm.
│   ├── views.py                      Logica de todas las paginas + texto WhatsApp.
│   ├── urls.py                       Direcciones de la app.
│   ├── admin.py                      Panel de administracion (con inlines).
│   ├── apps.py / tests.py / __init__.py
│   ├── migrations\                   Historial de cambios de la BD:
│   │   ├── 0001_initial.py              Tabla Incidente.
│   │   ├── 0002_alter_...py             como_se_detecto (desplegable) + reporte_inicial.
│   │   ├── 0003_avance.py               Tabla Avance.
│   │   └── 0004_area_persona.py         Tablas Area y Persona.
│   └── templates\
│       ├── base.html                 Plantilla base (barra superior + enlace al CSS).
│       └── incidentes\
│           ├── inicio.html              Pantalla de inicio (3 tarjetas).
│           ├── lista.html               Notificaciones en tarjetas + filtro.
│           ├── crear.html               Formulario de nueva notificacion (2 columnas).
│           ├── detalle.html             Ver: datos + areas/personas/avances + WhatsApp.
│           ├── actualizar.html          Generar Actualizacion / Resolver + WhatsApp.
│           └── dashboard.html           Dashboard gerencial (basico, se ampliara).
│
├── static\
│   └── style.css                  <- Estilos (tema oscuro, tarjetas, botones, WhatsApp).
│
├── manage.py                      <- "Control remoto": python manage.py <orden>.
├── .env                           <- SECRETOS (contraseña, host Supabase). NO se sube.
├── .gitignore                     <- Lo que Git nunca sube (.env, venv, db.sqlite3).
├── db.sqlite3                     <- Base local vieja (ya no se usa; usamos Supabase).
└── GUIA_DEL_PROYECTO.md           <- Este documento.
```

### Regla mental para ubicarte
- ¿Cómo se ven los DATOS? -> incidentes\models.py
- ¿Qué hace cada PAGINA? -> incidentes\views.py
- ¿Qué dirección muestra qué? -> incidentes\urls.py (y config\urls.py)
- ¿Cómo se ve la pantalla? -> incidentes\templates\...
- ¿Estilos/colores? -> static\style.css
- ¿Ajustes generales / base de datos? -> config\settings.py
- ¿Secretos (contraseñas)? -> .env

---

## LO QUE HACE LA APLICACIÓN HOY

### Pantallas y direcciones (urls)
- `/`                         -> INICIO: 3 tarjetas (Crear, Notificaciones, Dashboard).
- `/notificaciones/`          -> Lista de notificaciones en TARJETAS con filtro
                                 (Solo abiertos / Solo resueltos / Todos).
- `/dashboard/`               -> Dashboard gerencial (contadores básicos por ahora).
- `/nuevo/`                   -> Formulario para crear una notificación.
- `/<id>/`                    -> VER: detalle completo + vista previa WhatsApp.
- `/<id>/actualizar/`         -> Generar Actualización (agregar avance / ticket).
- `/<id>/resolver/`           -> Resolver (cierra la notificación).

### Modelo de datos (tablas en Supabase)
- Incidente: incidente, ticket, prioridad, estado, afectacion_cliente,
  como_se_detecto (desplegable), reporte_inicial ("Cómo se detectó el incidente"),
  asignado_a, descripcion, solucion, hora_inicio, fecha_cierre, fecha_creacion.
- Avance: pertenece a un incidente (texto + hora). Relación uno a muchos.
- Area: pertenece a un incidente (nombre). Se eligen con casillas de una lista fija.
- Persona: pertenece a un incidente (nombre). Se escriben separadas por comas.

### Funcionalidades implementadas
- Crear notificación (formulario en 2 columnas; solución al final).
- Áreas por CASILLAS (lista fija de 23 áreas). Personas por texto separado por comas.
- Ver detalle con vista previa de WhatsApp (opción: todos los avances o solo el último).
- Generar Actualización: agrega avance y permite AGREGAR/EDITAR el ticket
  (útil cuando al inicio aún no se tiene el número de ticket).
- Resolver: cierra la notificación, guarda solución y fecha de cierre.
  No pide avance; muestra la descripción de la falla.
- Vista previa de WhatsApp en vivo (se arma al escribir) en actualizar/resolver.
- Botón "Copiar plantilla": copia el texto Y guarda (envía el formulario).
- Etiquetas en NEGRITA de WhatsApp: van entre asteriscos (*texto*).
- Hora en formato 24h (militar), convertida a zona horaria de Honduras.
- En la lista se muestra el TICKET (no el id interno). Si no hay ticket: "Por generarse".
- Filtro "Todos": primero los abiertos, luego los cerrados (no se mezclan).
- Iconos de acción en tarjetas: 👁 Ver, ✎ Actualizar, ✔ Resolver (con tooltip).

---

## HISTORIAL DE PASOS (resumen)

- PASO 1 ✅ Entorno: venv + Django instalados.
- PASO 2 ✅ Proyecto Django creado (config + manage.py).
- PASO 3 ✅ App "incidentes" creada y registrada. Idioma es-hn, hora America/Tegucigalpa.
- PASO 4 ✅ Modelo Incidente + migraciones.
- PASO 5 ✅ Panel de administración + superusuario.
- PASO 6 ✅ Conexión a Supabase (proyecto de DESARROLLO, no producción).
           psycopg + python-dotenv; .env con credenciales (Session pooler / IPv4).
- PASO 7 🔶 Pantallas de la app (EN CURSO / casi completo):
           inicio, lista en tarjetas + filtro, crear (2 columnas), detalle,
           actualizar, resolver, dashboard básico, vista previa WhatsApp, estilos CSS.

### Migraciones aplicadas
- 0001_initial, 0002 (como_se_detecto/reporte_inicial), 0003_avance, 0004_area_persona.

---

## COMANDOS ÚTILES (recordatorio)

Activar entorno (siempre, al abrir una terminal nueva):
```
.\venv\Scripts\Activate.ps1
```

Encender el servidor de desarrollo:
```
python manage.py runserver
```
(abrir http://127.0.0.1:8000/  ; detener con Ctrl + C)

Aplicar cambios de modelos:
```
python manage.py makemigrations
python manage.py migrate
```

Crear un usuario administrador:
```
python manage.py createsuperuser
```

---

## PENDIENTES (próximos pasos)

- Afinar diseño (colores, dos columnas formulario + WhatsApp lado a lado, etc.).
- Dashboard gerencial con gráficos/indicadores reales.
- Revisar si "Resolver" debe permitir editar ticket también.
- Empaquetar con Docker.
- Desplegar con Terraform.
- Instalar git antes de desplegar (aún no está instalado).
