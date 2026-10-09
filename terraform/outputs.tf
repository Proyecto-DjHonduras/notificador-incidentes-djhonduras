# ============================================================
# outputs.tf
# ------------------------------------------------------------
# Los "outputs" son datos que Terraform MUESTRA al terminar un
# apply. Sirven para ver información útil sin buscarla a mano
# en la consola de AWS (por ejemplo, la URL del repositorio ECR
# donde subiremos la imagen).
# ============================================================

# output -> declara un dato a mostrar.
# "ecr_repository_url" es el nombre del output.
output "ecr_repository_url" {
  description = "URL del repositorio ECR (se usa para subir la imagen con docker push)."
  # Tomamos el atributo "repository_url" del recurso ECR que creamos.
  # Sintaxis: tipo.nombre_interno.atributo
  value = aws_ecr_repository.app.repository_url
}

# URL pública de la app, que da App Runner al crear el servicio.
# Es la dirección donde se podrá abrir la aplicación en el navegador.
output "app_url" {
  description = "URL pública de la aplicación en App Runner."
  # App Runner entrega el dominio sin 'https://', así que lo anteponemos.
  value = "https://${aws_apprunner_service.app.service_url}"
}
