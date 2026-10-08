# ============================================================
# variables.tf
# ------------------------------------------------------------
# Aquí DECLARAMOS las variables (las "casillas vacías").
# Los VALORES reales se ponen en terraform.tfvars (que NO se
# sube a git porque contiene secretos como la contraseña).
#
# Cada variable tiene:
#   - description: para qué sirve (documentación).
#   - type: qué tipo de dato acepta (string = texto).
#   - default: valor por defecto (opcional). Si no hay default,
#     el valor es OBLIGATORIO y debe darse en terraform.tfvars.
#   - sensitive: si es true, Terraform OCULTA el valor en pantalla
#     (se usa para secretos como contraseñas).
# ============================================================

# --- Configuración general ---

variable "region" {
  description = "Región de AWS donde se crea la infraestructura."
  type        = string
  default     = "us-east-1"
}

variable "proyecto" {
  description = "Nombre del proyecto, se usa para nombrar los recursos."
  type        = string
  default     = "notificador-incidentes"
}

# --- Variables de la aplicación Django ---
# Son las mismas que la app ya lee del entorno (como en Render).

variable "debug" {
  description = "Modo DEBUG de Django. En producción debe ser False."
  type        = string
  default     = "False"
}

variable "secret_key" {
  description = "SECRET_KEY de Django (clave secreta de la app)."
  type        = string
  sensitive   = true # es un secreto: se oculta en pantalla
}

variable "allowed_hosts" {
  description = "Hosts permitidos por Django (dominio público de la app)."
  type        = string
  # Sin default: su valor dependerá de la URL que nos dé App Runner.
  # Al inicio lo dejaremos amplio y luego lo ajustamos.
  default     = "*"
}

# --- Variables de la base de datos (Supabase / PostgreSQL) ---

variable "db_name" {
  description = "Nombre de la base de datos."
  type        = string
}

variable "db_user" {
  description = "Usuario de la base de datos."
  type        = string
}

variable "db_password" {
  description = "Contraseña de la base de datos (SECRETO)."
  type        = string
  sensitive   = true # secreto: no se muestra en pantalla
}

variable "db_host" {
  description = "Host/servidor de la base de datos (Supabase)."
  type        = string
}

variable "db_port" {
  description = "Puerto de la base de datos."
  type        = string
  default     = "5432"
}

variable "db_sslmode" {
  description = "Modo SSL de conexión a la base (Supabase requiere SSL)."
  type        = string
  default     = "require"
}
