#!/usr/bin/env bash
# Script que Render ejecuta durante el "build" (antes de arrancar la app).
# 'set -o errexit' hace que el build falle si cualquier comando falla.
set -o errexit

# 1) Instalar las dependencias del proyecto.
pip install -r requirements.txt

# 2) Recolectar los archivos estáticos (CSS/JS) en STATIC_ROOT.
python manage.py collectstatic --no-input

# 3) Aplicar las migraciones a la base de datos (Supabase).
python manage.py migrate
