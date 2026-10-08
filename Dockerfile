# ============================================================
# Dockerfile: instrucciones para construir la IMAGEN de la app.
# Docker lee este archivo de arriba hacia abajo y arma la "caja".
# ============================================================

# 1) IMAGEN BASE
#    Partimos de una imagen oficial de Python 3.12 "slim" (ligera).
#    Es como decir: "mi caja arranca con Linux + Python 3.12 ya instalados".
FROM python:3.12-slim

# 2) VARIABLES DE ENTORNO para que Python se comporte bien en contenedores.
#    PYTHONDONTWRITEBYTECODE: no crear archivos .pyc (basura innecesaria).
#    PYTHONUNBUFFERED: que los logs salgan al instante (no se queden en buffer).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3) CARPETA DE TRABAJO dentro de la caja.
#    A partir de aquí, todo ocurre dentro de /app en el contenedor.
WORKDIR /app

# 4) INSTALAR DEPENDENCIAS DEL SISTEMA que psycopg (PostgreSQL) necesita.
#    libpq5 es la librería cliente de PostgreSQL. Luego limpiamos la caché
#    de apt para que la imagen quede más liviana.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 5) INSTALAR LIBRERÍAS DE PYTHON.
#    Copiamos PRIMERO solo requirements.txt (no todo el código). Así, si el
#    código cambia pero las dependencias no, Docker reutiliza esta capa y
#    la construcción es mucho más rápida (esto se llama "cache de capas").
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 6) COPIAR EL RESTO DEL CÓDIGO del proyecto a la caja.
#    El punto "." significa "todo lo del proyecto" (respetando .dockerignore).
COPY . .

# 7) RECOLECTAR ARCHIVOS ESTÁTICOS (CSS/JS) para servirlos con WhiteNoise.
#    --no-input evita que pregunte nada durante la construcción.
RUN python manage.py collectstatic --no-input

# 8) PUERTO que la app expondrá dentro del contenedor.
#    Gunicorn escuchará en el 8080 (puerto que luego usará App Runner).
EXPOSE 8080

# 9) COMANDO DE ARRANQUE del contenedor.
#    Al iniciar la caja, se ejecuta gunicorn sirviendo la app Django.
#    config.wsgi:application apunta a tu archivo config/wsgi.py.
#    --bind 0.0.0.0:8080 hace que acepte conexiones desde fuera del contenedor.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080"]
