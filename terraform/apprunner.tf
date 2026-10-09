# ============================================================
# apprunner.tf
# ------------------------------------------------------------
# Crea el servicio App Runner, que TOMA la imagen del ECR y la
# CORRE (le pone URL pública y HTTPS). Es el equivalente a Render.
#
# Necesita 2 cosas que también creamos aquí:
#   1) Un ROL IAM que permita a App Runner leer imágenes del ECR.
#   2) El servicio App Runner en sí (con el puerto y las variables).
# ============================================================


# ------------------------------------------------------------
# 1) ROL IAM: permiso para que App Runner acceda a ECR
# ------------------------------------------------------------
# "assume_role_policy" define QUIÉN puede usar este rol.
# Aquí decimos: el servicio "build.apprunner.amazonaws.com"
# (el componente de App Runner que descarga imágenes) puede asumirlo.
resource "aws_iam_role" "apprunner_ecr_access" {
  name = "${var.proyecto}-apprunner-ecr-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })
}

# Adjuntamos al rol una política YA EXISTENTE de AWS que da permiso
# de solo lectura sobre ECR (justo lo que App Runner necesita para
# descargar la imagen). No reinventamos la rueda: AWS ya la provee.
resource "aws_iam_role_policy_attachment" "apprunner_ecr_access" {
  role       = aws_iam_role.apprunner_ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}


# ------------------------------------------------------------
# 2) SERVICIO APP RUNNER
# ------------------------------------------------------------
resource "aws_apprunner_service" "app" {
  # Nombre del servicio en AWS.
  service_name = var.proyecto

  # --- De dónde saca la app y cómo la corre ---
  source_configuration {
    # Autenticación para acceder al ECR (usa el rol de arriba).
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }

    # Que App Runner NO redepliegue solo al cambiar la imagen.
    # (Lo controlamos nosotros con Terraform / push manual.)
    auto_deployments_enabled = false

    image_repository {
      # La imagen que creamos y subimos al ECR, con el tag "latest".
      image_identifier      = "${aws_ecr_repository.app.repository_url}:latest"
      image_repository_type = "ECR"

      image_configuration {
        # Puerto donde escucha la app DENTRO del contenedor (gunicorn:8080).
        port = "8080"

        # Variables de entorno que recibe la app (las mismas que en Render).
        # Se arman desde las variables de Terraform (que vienen del tfvars).
        runtime_environment_variables = {
          DEBUG         = var.debug
          SECRET_KEY    = var.secret_key
          ALLOWED_HOSTS = var.allowed_hosts
          DB_NAME       = var.db_name
          DB_USER       = var.db_user
          DB_PASSWORD   = var.db_password
          DB_HOST       = var.db_host
          DB_PORT       = var.db_port
          DB_SSLMODE    = var.db_sslmode
        }
      }
    }
  }

  # --- Recursos de cómputo (tamaño del servidor) ---
  # El más pequeño disponible: 0.25 vCPU y 0.5 GB RAM. Suficiente y económico.
  instance_configuration {
    cpu    = "256"  # 0.25 vCPU (en milésimas: 256 = 0.25)
    memory = "512"  # 0.5 GB RAM
  }

  # --- Chequeo de salud ---
  # Usamos TCP: App Runner solo comprueba que el puerto 8080 ACEPTE conexión,
  # sin hacer una petición HTTP. Esto es importante porque la app tiene
  # SECURE_SSL_REDIRECT=True (con DEBUG=False), que redirige las peticiones
  # HTTP a HTTPS con un 301; un health check HTTP interno recibiría ese 301 y
  # marcaría la app como "no sana", reiniciándola en bucle. Con TCP se evita.
  health_check_configuration {
    protocol            = "TCP"
    interval            = 10 # cada 10 s
    timeout             = 5  # espera hasta 5 s
    healthy_threshold   = 1  # 1 OK = sano
    unhealthy_threshold = 5  # 5 fallos seguidos = no sano
  }
}
