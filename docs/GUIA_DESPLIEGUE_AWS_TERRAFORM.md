# Guía: Desplegar el Notificador de Incidentes en AWS con Docker + Terraform

> Documento de aprendizaje. Registra paso a paso el proceso de llevar la aplicación
> Django a AWS usando contenedores (Docker) e Infraestructura como Código (Terraform).
> Pensado para alguien que parte desde cero en estos temas.

---

## Índice

- [Conceptos base](#conceptos-base)
- [Arquitectura objetivo](#arquitectura-objetivo)
- [Plan por fases](#plan-por-fases)
- [FASE 0 — Cuenta AWS y seguridad](#fase-0--cuenta-aws-y-seguridad)
- [FASE 1 — Contenerizar con Docker](#fase-1--contenerizar-con-docker)
- [FASE 2 — AWS CLI y Terraform](#fase-2--aws-cli-y-terraform)
- [FASE 3 — Infraestructura con Terraform](#fase-3--infraestructura-con-terraform)
- [FASE 4 — Buenas prácticas](#fase-4--buenas-practicas)
- [FASE 5 — CI/CD (opcional)](#fase-5--cicd-opcional)
- [Glosario](#glosario)

---

## Conceptos base

Tres piezas, explicadas con una analogía de "abrir un restaurante":

1. **Docker** = meter tu receta y todos los ingredientes en una **caja sellada** que
   funciona igual en cualquier cocina. Tu "caja" es la app Django lista para correr.
2. **La nube (AWS)** = el **local** que alquilas donde pondrás tu cocina.
3. **Terraform** = las **instrucciones escritas** de cómo montar el local. Lo escribes
   una vez y el local se monta solo, siempre igual (esto es "Infraestructura como Código").

**Infraestructura como Código (IaC):** en vez de crear servidores a mano haciendo clics,
se escriben archivos de texto que describen la infraestructura. Ventajas: reproducible,
versionable en git, y reversible.

---

## Arquitectura objetivo

Flujo que vamos a construir:

```
   APP DJANGO (ya existe, hoy en Render)
          |
          v
   [1] DOCKER: se empaqueta en una "imagen"
          |
          v
   [2] ECR (Elastic Container Registry): se sube la imagen a AWS
          |
          v
   [3] APP RUNNER: toma la imagen y la corre, con HTTPS y URL pública
          |          (recibe las variables de entorno de Supabase)
          v
   APP CORRIENDO EN AWS
```

Servicios de AWS que usaremos:
- **ECR** = el "GitHub de imágenes Docker". Guarda la app empaquetada.
- **App Runner** = corre el contenedor y lo publica. Es lo más simple de AWS para esto
  (equivalente a lo que hacía Render).
- La **base de datos sigue en Supabase** (no cambia).

---

## Plan por fases

- **FASE 0** — Cuenta AWS y seguridad (MFA, usuario IAM, alerta de presupuesto).
- **FASE 1** — Contenerizar la app con Docker y probarla en local.
- **FASE 2** — Instalar AWS CLI y Terraform; aprender init/plan/apply/destroy.
- **FASE 3** — Crear con Terraform: ECR + App Runner + variables de Supabase.
- **FASE 4** — Buenas prácticas: secretos, estado remoto, destroy, versionar en GitHub.
- **FASE 5** — (Opcional) CI/CD con GitHub Actions y módulos de Terraform.

---

## FASE 0 — Cuenta AWS y seguridad

Objetivo: tener una cuenta de AWS asegurada y un usuario para que Terraform trabaje.

### Conceptos de esta fase

- **Cuenta root (raíz):** la cuenta principal, dueña de todo. NO se usa para el trabajo
  diario. Solo para configuración inicial; luego se guarda "bajo llave".
- **Usuario IAM:** usuario secundario con permisos, para el día a día y para Terraform.
- **MFA (doble factor):** además de la contraseña, pide un código temporal del celular.
- **Access Keys:** par de llaves (Access Key ID + Secret Access Key) que usan los
  programas (como Terraform) para autenticarse en AWS.

### Pasos realizados

- [x] **Verificado:** ya existía una cuenta AWS real (distinta del "AWS Builder ID",
  que NO sirve para desplegar). Se confirmó entrando a `console.aws.amazon.com`.
- [x] **MFA activado en la cuenta root** con una app autenticadora (Authenticator app).
  Se registró un dispositivo virtual y se verificó la información de recuperación
  (correo y teléfono).
- [x] **Usuario IAM creado:** `terraform-admin` con política `AdministratorAccess`.
- [x] **Access Keys creadas** (caso de uso CLI) y guardadas en un archivo `.csv` FUERA
  del proyecto. Nunca se suben a GitHub ni se comparten.
- [ ] **Configurar alerta de presupuesto** (Budget) para evitar gastos sorpresa.

### Access Keys — reglas de oro

- El **Secret Access Key** solo se muestra una vez al crearlo.
- NUNCA se suben a GitHub, ni se escriben en documentos, ni se pegan en chats.
- Se guardan en un gestor de contraseñas o un `.csv` fuera de la carpeta del proyecto.
- Se usan para que Terraform / AWS CLI se autentiquen en AWS.

### Cómo crear el usuario IAM (paso a paso)

1. En la consola de AWS, buscar **IAM** en la barra superior y entrar.
2. Menú izquierdo → **Users** → botón **Create user**.
3. **User name:** `terraform-admin`.
4. NO marcar "Provide user access to the AWS Management Console"
   (este usuario solo lo usa Terraform, no entra por la web).
5. **Next**.
6. Permisos → **Attach policies directly** → buscar y marcar **AdministratorAccess**.
   - Nota: en producción se usan permisos más acotados (mínimo privilegio).
     Para aprender se usa AdministratorAccess y así no faltan permisos.
7. **Next** → **Create user**.

> Pendiente de documentar: creación de Access Keys y alerta de presupuesto.

---

## Nota: entorno de práctica

Esta cuenta de AWS es un **laboratorio personal de aprendizaje** (la empresa aún no
provee los recursos). Todo lo que se aprende aquí es transferible: Terraform, Docker,
ECR, App Runner y RDS funcionan igual en una cuenta de empresa; solo cambian las
credenciales y los nombres. El código Terraform es reutilizable.

Reglas del laboratorio:
- Cuidar costos: usar capa gratuita y `terraform destroy` al terminar cada práctica.
- No usar datos reales/sensibles de la empresa en la cuenta personal.
- Las credenciales de la cuenta personal son distintas de las de la empresa; no mezclar.

---

## FASE 1 — Contenerizar con Docker

Objetivo: empaquetar la app Django en una imagen Docker y probarla en local.

### Conceptos de esta fase

- **Docker:** el programa gestor. En un mismo Docker pueden correr VARIAS "cajas"
  (contenedores) a la vez, aisladas entre sí.
- **Imagen:** la "caja sellada" (plantilla estática) con la app + Python + librerías.
  Es como un archivo de instalación.
- **Contenedor:** una imagen EN EJECUCIÓN. De una imagen se pueden crear muchos
  contenedores idénticos.
- **Dockerfile:** archivo de texto con las instrucciones para construir la imagen.
- **.dockerignore:** lista de archivos/carpetas que NO se copian a la imagen
  (equivalente al .gitignore, pero para Docker).

En este proyecto: 1 imagen (la app Django) y 1 contenedor. La base de datos NO va en
contenedor (está en Supabase, externo).

### Pasos

- [x] Crear `Dockerfile` en la raíz del proyecto.
- [x] Crear `.dockerignore` en la raíz del proyecto.
- [~] Instalar Docker Desktop: BLOQUEADO. El equipo no tiene permisos de administrador
      y no se puede activar "Virtual Machine Platform" (requisito de WSL 2). Docker
      Desktop quedó instalado pero el motor no arranca.
- [x] **Decisión:** construir la imagen en **AWS CloudShell** (terminal Linux gratuita
      en el navegador, con Docker ya incluido). No requiere instalar nada en el PC
      ni permisos de admin.

### Por qué CloudShell

- Es una terminal Linux dentro de la consola de AWS (en el navegador).
- Ya trae Docker, AWS CLI y Git instalados.
- Permite construir la imagen y subirla a ECR con los comandos Docker reales.
- No necesita virtualización ni permisos locales.
- Es gratis (incluye almacenamiento persistente de 1 GB en el home).

### Plan con CloudShell (se ejecuta en la Fase 3)

1. Abrir CloudShell desde la consola de AWS (icono de terminal, arriba a la derecha).
2. Clonar el repositorio del proyecto desde GitHub.
3. `docker build` para construir la imagen (comando Docker real).
4. Subir la imagen al repositorio ECR (que creará Terraform).
5. App Runner la toma y la corre.

---

## FASE 2 — AWS CLI y Terraform

Objetivo: tener Terraform funcionando y aprender su ciclo de vida con un ejemplo mínimo
(crear un bucket de S3 y luego destruirlo).

### Decisión: trabajar en CloudShell (no en el PC local)

Como el PC no tiene permisos de administrador, en vez de instalar AWS CLI y Terraform
localmente, se usa **AWS CloudShell** para todo. Ventajas:
- No requiere permisos de admin ni virtualización.
- CloudShell ya está autenticado con la cuenta AWS: **no hay que configurar Access Keys**.
- Es el mismo entorno donde se construirá la imagen Docker (todo en un solo lugar).

### Los 4 comandos del ciclo de vida de Terraform

| Comando | Qué hace |
|---------|----------|
| `terraform init` | Prepara la carpeta y descarga el provider (plugin) de AWS. Se corre al inicio. |
| `terraform plan` | Muestra qué va a crear/cambiar/borrar, SIN hacerlo. Es el "ensayo". |
| `terraform apply` | Ejecuta los cambios: crea la infraestructura de verdad (pide escribir `yes`). |
| `terraform destroy` | Borra todo lo que Terraform creó. |

Regla de oro: `plan` antes de `apply`; `destroy` al terminar la práctica (para no gastar).

Símbolos del plan: `+` crear, `~` modificar, `-` destruir.
`(known after apply)` = valor que AWS asigna recién al crear el recurso (normal).

### Otros conceptos

- **Provider:** plugin que conecta Terraform con una nube (aquí, `aws`).
- **Resource:** cada cosa que se crea (ej. un bucket S3).
- **State** (`terraform.tfstate`): archivo donde Terraform anota qué creó. Puede tener
  datos sensibles; NO se sube a GitHub.

### Pasos realizados

- [x] **Instalar Terraform en CloudShell** (descarga del `.zip`, descomprimir, mover a
  `~/bin`, agregar al PATH). Versión instalada: **Terraform v1.9.8**.
  - El aviso "Your version is out of date" se ignora: 1.9.8 es estable para aprender.
- [x] **Crear carpeta de práctica** `~/practica-terraform` con un `main.tf` que define
  un `provider "aws"` (región us-east-1) y un recurso `aws_s3_bucket`.
- [x] `terraform init` → "Terraform has been successfully initialized!".
- [x] `terraform plan` → `Plan: 1 to add, 0 to change, 0 to destroy`.
- [x] `terraform apply` → bucket creado (`Apply complete! Resources: 1 added`).
- [x] `terraform destroy` → bucket eliminado (`Destroy complete! Resources: 1 destroyed`).

### Conceptos aprendidos con el ejercicio

- **Declarativo:** en el `.tf` describes el ESTADO que quieres ("que exista un bucket así"),
  no los pasos. Terraform logra ese estado.
- **Idempotente:** correr `apply` varias veces no duplica ni rompe nada. Si la realidad ya
  coincide con el código, Terraform no hace nada ("No changes / 0 added").
- **State (`terraform.tfstate`):** la "memoria" de Terraform. Guarda qué creó. En cada
  `plan`/`apply` hace "Refreshing state": compara su memoria + el estado real en AWS + tu
  código, y actúa solo sobre las diferencias. Vive en la carpeta del proyecto (en CloudShell,
  dentro de la HOME, por eso persistió entre sesiones).
- **Confirmaciones:** `apply` y `destroy` piden escribir `yes`. `destroy` avisa
  "There is no undo" porque es irreversible.

> Situación vivida: al volver al día siguiente, `plan`/`apply` dijeron "No changes / 0 added"
> porque el bucket ya existía (creado el día anterior). Es el comportamiento correcto: la
> realidad ya coincidía con el código. No es un error.

### Comandos usados (referencia)

```bash
# Instalar Terraform en CloudShell
cd ~
wget -q https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_linux_amd64.zip
unzip -o terraform_1.9.8_linux_amd64.zip
mkdir -p ~/bin
mv -f terraform ~/bin/
export PATH=$PATH:~/bin
terraform version

# Hacer el PATH permanente entre sesiones de CloudShell
echo 'export PATH=$PATH:~/bin' >> ~/.bashrc

# Ciclo de Terraform (dentro de ~/practica-terraform)
terraform init
terraform plan
# terraform apply   (escribir 'yes' para confirmar)
# terraform destroy (escribir 'yes' para confirmar)
```

### Problema encontrado y solución (IMPORTANTE)

**Síntoma:** tras un rato, la sesión de CloudShell se reinició. Al volver:
- `cd ~/practica-terraform` dio "No such file or directory" (la terminal arrancó en otra
  ruta; la carpeta sí existía).
- `terraform: command not found` y `~/bin` había desaparecido.

**Causa:** CloudShell conserva de forma persistente el contenido de la carpeta HOME (`~`),
pero el **PATH se reinicia** en cada sesión nueva, y en este caso también se había perdido
el binario de `~/bin`. Las variables de entorno (como el PATH) NO sobreviven entre sesiones
salvo que se dejen en `~/.bashrc`.

**Solución aplicada:**
1. Reinstalar Terraform (volver a bajar, descomprimir y mover a `~/bin`).
2. Agregar el PATH a `~/.bashrc` con:
   `echo 'export PATH=$PATH:~/bin' >> ~/.bashrc`
   Así, en cada sesión nueva de CloudShell, Terraform queda disponible automáticamente.

**Lección:** en CloudShell, todo lo que deba persistir va en la HOME, y las variables de
entorno se dejan en `~/.bashrc`. Si en el futuro `terraform` no responde, basta con:
`export PATH=$PATH:~/bin` (o reabrir la terminal para que `.bashrc` lo cargue solo).

---

## FASE 3 — Infraestructura con Terraform

Objetivo: crear la infraestructura real de la app en AWS con Terraform:
primero el **ECR** (bodega de imágenes) y después **App Runner** (corre la app).

### Terraform vs. Render vs. App Runner (aclaración clave)

- **Render** (hoy) = aloja y CORRE la app.
- **App Runner** (AWS) = el equivalente a Render: alojará y correrá la app.
- **ECR** (AWS) = la bodega donde se guarda la imagen Docker (la "caja").
- **Terraform** = NO corre la app; es el "constructor" que CREA App Runner, ECR y
  permisos, escribiéndolo como código (en vez de hacer clics como en Render).

Resumen: App Runner reemplaza a Render; Terraform es la herramienta que lo construye.

### Repaso: imagen vs. ECR

- **Imagen** = la "caja" con la app empaquetada (concepto de la Fase 1).
- **ECR** = la bodega de AWS donde se GUARDA esa caja. App Runner la saca de ahí y la
  ejecuta (contenedor). ECR es a las imágenes lo que GitHub es al código.

### Sintaxis de Terraform (HCL)

Bloques con forma: `TIPO "etiqueta" { argumento = valor }`. Los principales:
- `provider` → configura la conexión a una nube.
- `resource "tipo" "nombre_interno"` → crea algo (lleva tipo + apodo interno).
- `variable "x"` → declara una "casilla" para un valor.
- Para USAR una variable: `var.x`.
- Para referir un recurso: `tipo.nombre_interno.atributo`.

### Lógica de la carpeta `terraform/`

- Terraform lee TODOS los `.tf` de la carpeta como si fueran UN SOLO archivo.
- Separar en varios archivos es solo por ORDEN humano (no cambia el resultado).
- Los archivos se CONECTAN por referencias (`var.x`, `tipo.nombre.atributo`).
- El ORDEN de archivos/bloques NO importa: Terraform calcula solo las dependencias
  (grafo de dependencias). Sabe que para el output del ECR, primero crea el ECR.
- La carpeta va DENTRO del proyecto para tener app + infraestructura en el mismo repo.

Archivos creados en `terraform/`:

| Archivo | Para qué | ¿Sube a git? |
|---------|----------|--------------|
| `providers.tf` | Configura AWS y el plugin (provider) | Sí |
| `variables.tf` | Declara las variables ("casillas") | Sí |
| `ecr.tf` | Crea el repositorio ECR (bodega de imágenes) | Sí |
| `outputs.tf` | Muestra la URL del ECR al terminar | Sí |
| `terraform.tfvars.example` | Plantilla de valores (SIN secretos) | Sí |
| `.gitignore` | Protege secretos y archivos internos | Sí |
| `terraform.tfvars` | Valores REALES con secretos | **NO** (se crea en CloudShell) |

Cómo se conectan (ejemplo real):
- `variables.tf` define `region` y `proyecto`.
- `providers.tf` usa `var.region` para saber dónde crear.
- `ecr.tf` usa `var.proyecto` para nombrar el repositorio.
- `outputs.tf` saca `aws_ecr_repository.app.repository_url` del recurso de `ecr.tf`.

### Variables y secretos (`.tfvars`)

- `variables.tf` = las "casillas vacías" (declaración). No tiene valores reales.
- `terraform.tfvars` = las casillas RELLENAS con valores reales (incluye secretos).
- Variables con `sensitive = true` (ej. `secret_key`, `db_password`) se OCULTAN en pantalla.
- Por ahora los secretos van en `terraform.tfvars` (simple, para aprender). Ese archivo
  NO sube a git. En la FASE 4 se mejora usando AWS Secrets Manager (lo profesional).

### Flujo de trabajo (GitHub ↔ CloudShell ↔ AWS)

```
  TU PC (escribes los .tf)
     | git push
     v
  GITHUB (guarda los "planos" .tf)
     | git clone / pull
     v
  CLOUDSHELL (tiene Terraform) --- terraform init/plan/apply --->  AWS construye ECR
```

Los `.tf` son solo "planos"; no construyen nada solos. Terraform (en CloudShell) los lee
y le ordena a AWS crear los recursos.

### Pasos realizados

- [x] Crear carpeta `terraform/` con: providers.tf, variables.tf, ecr.tf, outputs.tf,
  terraform.tfvars.example y .gitignore (bien comentados).
- [x] Subir los `.tf` a GitHub (`git push`). Commit "Agregar infraestructura Terraform".
- [x] CloudShell: clonar el repo (`git clone`).
- [x] CloudShell: crear `terraform.tfvars` con los valores reales (secretos).
- [x] CloudShell: `terraform init / plan / apply` → **ECR creado**.
  - URL del ECR: `032916962499.dkr.ecr.us-east-1.amazonaws.com/notificador-incidentes`
- [x] Construir la imagen Docker (`docker build`) y subirla al ECR (`docker push`).
  - Imagen de 193 MB subida con tag `latest`.
- [ ] Agregar App Runner (siguiente tanda) y obtener la URL pública.

### Comandos usados (ECR + imagen)

```bash
# En ~/notificador-incidentes-djhonduras/terraform
terraform init
terraform plan
terraform apply   # escribir 'yes'
# Output: ecr_repository_url = 032916962499.dkr.ecr.us-east-1.amazonaws.com/notificador-incidentes

# Autenticar Docker con ECR
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin 032916962499.dkr.ecr.us-east-1.amazonaws.com

# Construir, etiquetar y subir la imagen (desde la raiz del repo, donde esta el Dockerfile)
cd ~/notificador-incidentes-djhonduras
docker build -t notificador-incidentes .
docker tag notificador-incidentes:latest 032916962499.dkr.ecr.us-east-1.amazonaws.com/notificador-incidentes:latest
docker push 032916962499.dkr.ecr.us-east-1.amazonaws.com/notificador-incidentes:latest
```

### Problema encontrado y solución: "no space left on device"

**Síntoma:** `terraform init` falló al instalar el provider de AWS con el error
`no space left on device`, pese a que `df -h /home` mostraba 9 GB libres.

**Causa real:** el almacenamiento PERSISTENTE de CloudShell (`/home/cloudshell-user`,
visto como `/dev/loop0`) es de solo **~1 GB** y estaba al 81%. Las particiones grandes
(16 GB, 30 GB) son del sistema y no cuentan para el home. El provider de AWS pesa cientos
de MB y no cabía.

**Solución aplicada:**
1. Borrar la carpeta de práctica anterior (`rm -rf ~/practica-terraform`, liberó 789 MB).
2. Borrar el `.zip` de Terraform ya usado (`rm -f ~/*.zip`).
3. CLAVE: mover el caché de providers a `/tmp` (partición grande del sistema):
   ```bash
   mkdir -p /tmp/tf-plugin-cache
   export TF_PLUGIN_CACHE_DIR=/tmp/tf-plugin-cache
   echo 'export TF_PLUGIN_CACHE_DIR=/tmp/tf-plugin-cache' >> ~/.bashrc
   ```
   Con esto el provider se descarga en `/tmp` (que no satura el home de 1 GB).

**Lección:** en CloudShell el home persistente es de ~1 GB. Para Terraform conviene mantener
`TF_PLUGIN_CACHE_DIR=/tmp/tf-plugin-cache`. Como `/tmp` se vacía entre sesiones, un `init`
futuro redescarga el provider (es aceptable). El repo clonado también ocupa espacio (incluía
`venv`), conviene no clonar carpetas pesadas innecesarias.

### Problema con nano (editar terraform.tfvars)

- Al guardar en nano, quedó atascado en "File Name to Write: terraform.tfvars". Solución:
  pulsar **Enter** (confirma el nombre) y luego **Ctrl+X** (salir).
- La `secret_key` había quedado con el placeholder. Se corrigió sin reabrir nano, generando
  una clave y reemplazando solo esa línea con `sed`:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(50))"
  sed -i 's|^secret_key.*|secret_key    = "LA_CLAVE_GENERADA"|' terraform.tfvars
  ```
- Verificar sin exponer secretos (muestra longitudes, no valores):
  ```bash
  awk -F'=' '/^(secret_key|db_user|db_password|db_host)/ {gsub(/ /,"",$1); print $1" -> "length($2)" caracteres"}' terraform.tfvars
  ```

> Estado: ECR creado y con la imagen dentro. La app en Render sigue intacta.
> Falta crear App Runner para que corra la imagen y dé la URL pública.

---

## FASE 3.5 — (Opcional) Migrar base de datos a Amazon RDS

Solo si la empresa pide reemplazar Supabase por una base PostgreSQL propia de AWS.

- **Amazon RDS:** servicio de base de datos PostgreSQL **gestionado** por AWS (respaldos,
  actualizaciones y disponibilidad los maneja AWS). NO es un contenedor; es un servicio
  aparte, igual que lo era Supabase.
- **Qué cambia en la app:** casi nada. Solo las variables `DB_HOST`, `DB_USER`,
  `DB_PASSWORD`, etc. apuntan a la nueva base. El código no cambia.
- **Qué cambia en infraestructura:** se agrega un `resource` de RDS en Terraform y la
  app se conecta por la red interna de AWS (más rápido y seguro que salir a internet).
- **Costo:** capa gratuita el primer año (`db.t3.micro`), no es "siempre gratis".
- **Migración de datos:** exportar de Supabase e importar a RDS (paso aparte).

---

## FASE 4 — Buenas prácticas

> Pendiente.

---

## FASE 5 — CI/CD (opcional)

> Pendiente.

---

## Glosario

- **AWS:** Amazon Web Services, la nube de Amazon.
- **AWS Builder ID:** perfil gratuito de aprendizaje de AWS. NO permite crear
  infraestructura. Es distinto de una "cuenta de AWS".
- **Cuenta de AWS (AWS Account):** la cuenta real con número de 12 dígitos y facturación,
  donde viven todos los servicios.
- **Consola de AWS:** el panel web (`console.aws.amazon.com`) para administrar servicios.
- **Root:** usuario dueño total de la cuenta. Uso mínimo, bien protegido.
- **IAM:** Identity and Access Management. Gestión de usuarios y permisos.
- **MFA:** Multi-Factor Authentication. Doble factor de seguridad.
- **Access Key / Secret Access Key:** credenciales para que programas accedan a AWS.
- **Docker:** herramienta para empaquetar la app en contenedores.
- **Imagen Docker:** la "caja sellada" con la app y su entorno.
- **Contenedor:** una imagen en ejecución.
- **ECR:** Elastic Container Registry. Almacén de imágenes Docker en AWS.
- **App Runner:** servicio de AWS que corre contenedores con URL pública y HTTPS.
- **Terraform:** herramienta de Infraestructura como Código.
- **Provider:** plugin de Terraform para una nube concreta (ej. AWS).
- **Resource:** cada recurso que Terraform crea (ej. un repositorio ECR).
- **State:** archivo donde Terraform recuerda qué recursos creó.
- **Free Tier:** capa gratuita de AWS con límites de uso sin costo.
```
