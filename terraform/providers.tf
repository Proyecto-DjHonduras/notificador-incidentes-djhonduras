# ============================================================
# providers.tf
# ------------------------------------------------------------
# Aquí configuramos QUÉ nube usa Terraform y de dónde saca el
# "provider" (el plugin que sabe comunicarse con esa nube).
# ============================================================

# Bloque "terraform": configuración general de la herramienta.
terraform {
  # required_version: exige una versión mínima de Terraform.
  # Así evitamos sorpresas si alguien usa una versión muy vieja.
  required_version = ">= 1.5"

  # required_providers: qué plugins necesita este proyecto.
  # Aquí pedimos el provider oficial de AWS, de HashiCorp.
  required_providers {
    aws = {
      source  = "hashicorp/aws" # de dónde se descarga el plugin
      version = "~> 6.0"        # usar la versión 6.x (6.0 o superior, menor que 7.0)
    }
  }
}

# Bloque "provider": configura el proveedor AWS en concreto.
# La región se toma de una variable (var.region) para poder
# cambiarla fácil sin tocar este archivo.
provider "aws" {
  region = var.region
}
