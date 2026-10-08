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
