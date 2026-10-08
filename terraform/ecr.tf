# ============================================================
# ecr.tf
# ------------------------------------------------------------
# Crea el repositorio ECR: la "bodega" de AWS donde se guardará
# la imagen Docker (la "caja") de la aplicación.
# App Runner luego sacará la imagen de aquí para ejecutarla.
# ============================================================

# resource -> crea algo en AWS.
# Tipo: aws_ecr_repository (un repositorio de imágenes).
# Nombre interno: "app" (para referirnos a él en otros archivos).
resource "aws_ecr_repository" "app" {
  # name: el nombre del repositorio como aparecerá en AWS.
  # Lo armamos con la variable del proyecto para mantener coherencia.
  name = var.proyecto

  # image_tag_mutability: si se permite sobrescribir una etiqueta de imagen.
  # MUTABLE = sí se puede (cómodo para aprender: subir "latest" varias veces).
  image_tag_mutability = "MUTABLE"

  # force_delete: permite borrar el repositorio aunque tenga imágenes dentro.
  # Útil en aprendizaje para que "terraform destroy" no falle por imágenes.
  force_delete = true

  # image_scanning_configuration: AWS puede escanear la imagen en busca de
  # vulnerabilidades al subirla. Lo activamos (es gratis y buena práctica).
  image_scanning_configuration {
    scan_on_push = true
  }
}
