# ⚖️ SGEJ — Sistema de Gestor de Expedientes Jurídicos
Arquitectura Modular del Software y Requerimientos  
**Estilo Arquitectónico:** Monolito Modular con Contextos Delimitados (*Bounded Contexts*)  
**Stack Tecnológico:** Django 5.2 + DRF + MySQL 8.0 + Bootstrap 5 + Criptografía AES/Fernet + Docker

---

## 🌟 Descripción General & Filosofía del Sistema

El **SGEJ (Sistema de Gestor de Expedientes Jurídicos)** es una plataforma monolítica modular de alto rendimiento desarrollada aplicando **Domain-Driven Design (DDD)** como metodología de diseño y modelado de dominio, estructurada sobre una arquitectura de **Monolito Modular**. Su propósito es automatizar, blindar y gestionar de manera integral el ciclo de vida completo de la gestión jurídica institucional.

Desde la recepción y clasificación de expedientes y la sustanciación de procedimientos disciplinarios hasta el cifrado forense de documentos *at-rest*, la firma digital con códigos QR y la bitácora de auditoría inmutable, el SGEJ garantiza rigor técnico, trazabilidad y cumplimiento de los más altos estándares de ingeniería de software moderna.

---

## 🛡️ Seguridad Avanzada y Cumplimiento (OWASP Top 10)

El **SGEJ** ha sido construido bajo ciberseguridad defensiva de nivel empresarial, alineándose con las directrices **OWASP Top 10** y aplicando mitigaciones avanzadas a nivel de aplicación e infraestructura:

- **Cifrado Criptográfico At-Rest (AES / Fernet)**: Todos los documentos y archivos binarios confidenciales son cifrados simétricamente antes de almacenarse en disco, impidiendo el acceso no autorizado sin la clave de cifrado institucional.
- **Bitácora de Auditoría Inmutable (SHA-256 Chained)**: Registro forense inalterable de todas las transacciones del sistema. Su inmutabilidad está garantizada en **dos niveles críticos**:
  1. *Nivel de Aplicación*: A través del `AuditoriaInmutableMiddleware`, que intercepta peticiones y prohíbe cualquier lógica de modificación (`UPDATE`) o eliminación (`DELETE`), permitiendo estrictamente operaciones de inserción (`INSERT`).
  2. *Nivel de Base de Datos*: Restricción de privilegios del usuario de conexión en MySQL (restringiendo permisos de actualización y borrado sobre la tabla `bitacora_auditoria`), configurando un almacenamiento de tipo *Append-Only Store*.
- **Autenticación de Doble Factor (2FA / TOTP)**: Integración nativa con generadores de códigos temporales (Google Authenticator, FreeOTP) para cuentas con privilegios administrativos.
- **Gestión de Identidad y RBAC Estricto**: Control de acceso basado en roles (`ADMIN`, `ABOG`, `USR_PUBLICO`) con aislamiento absoluto de datos mediante filtrado granular en consultas ORM (`BaseQuerySet`).
- **Protección contra Fuerza Bruta y Ataques**: Bloqueo automático de cuentas tras 3 intentos fallidos consecutivos de inicio de sesión, control de concurrencia de sesiones (`SessionControlMiddleware`) y limitación de peticiones (`RateLimiting`).
- **Sistema Honeypot de Intrusos**: Trampas virtuales integradas en rutas críticas para identificar y registrar accesos maliciosos o sondeos automatizados.
- **Seguridad de Credenciales**: Hashing con algoritmos de una sola vía (PBKDF2 / SHA-256) e historial inmutable de contraseñas que impide la reutilización de las últimas 3 claves.

---

## ⚙️ Arquitectura de Contextos Delimitados (*Bounded Contexts*)

Bajo los principios de **Domain-Driven Design (DDD)**, el sistema descompone el dominio del problema en **Contextos Delimitados (*Bounded Contexts*)** independientes y cohesivos, cada uno encapsulando su propio lenguaje ubicuo, modelos de dominio, reglas de negocio y servicios:

### 1. Bounded Context de Autenticación, Usuarios y Seguridad (`apps/usuarios`)
- **Propósito y Dominio**: Administra el ciclo de vida de la identidad y el acceso. Implementa el control de acceso basado en roles (RBAC: `ADMIN`, `ABOG`, `USR_PUBLICO`), autenticación de doble factor (2FA/TOTP), frase de seguridad para recuperación, políticas de contraseñas y la supervisión de intentos fallidos con bloqueo automático.

### 2. Bounded Context del Núcleo Jurídico y Procesal (`apps/expedientes`)
- **Propósito y Dominio**: Núcleo central del negocio jurídico. Modela expedientes, directorios de personal, cargos institucionales vinculados a marcos legales, motivos de reclamo, tribunales y la agenda de audiencias con notificaciones automatizadas. Gestiona formalmente el directorio de **Sujetos Procesales** (Defensores, Fiscales, Jueces, Secretarios y Contrapartes).

### 3. Bounded Context de Gestión Documental y Cifrado (`apps/documentos`)
- **Propósito y Dominio**: Controla la ingesta, almacenamiento y cifrado simétrico en disco (`AES-256 / Fernet`) de todos los archivos institucionales.
  - *Proceso de Descifrado, Búsqueda y Entrega*: Al solicitar la visualización o descarga, el servicio descifra el flujo binario en memoria RAM de manera efímera sin exponer archivos planos en el disco temporal, valida el hash de integridad `SHA-256`, serializa los metadatos y entrega el recurso con una latencia óptima menor a **300ms**.
  - *Procesamiento OCR*: Documentos escaneados, oficios físicos digitalizados y resoluciones en PDF sin capa de texto son procesados mediante **Tesseract OCR**, indexando su contenido en el campo `contenido_ocr` de MySQL para permitir búsquedas de texto completo eficientes.

### 4. Bounded Context de Biblioteca Legal y Normativa (`apps/biblioteca`)
- **Propósito y Dominio**: Repositorio institucional centralizado para almacenar y consultar normativas, reglamentos internos, resoluciones de consejo universitario y gacetas oficiales vinculables como sustento jurídico a los expedientes.

### 5. Bounded Context de Infraestructura Transversal (`apps/infraestructura`)
- **Propósito y Dominio**: Provee los servicios transversales de seguridad defensiva, control de límites de peticiones (*Rate Limiting*), control de sesiones concurrentes y el sistema trampa (*Honeypot*) para detección de intrusos.

---

## 📂 Submódulos y Tipos de Módulos de Expedientes (`tipo_modulo`)

En estricto apego al Lenguaje Ubicuo del dominio jurídico, el agregado raíz `Expediente` (`apps/expedientes`) clasifica la operatividad legal en **7 submódulos especializados**, organizados bajo principios de Clean Code:

1. **`DESP` — Calificación de Despido / Casos Recientes**:
   - *Dominio*: Gestión de expedientes urgentes relativos a solicitudes de calificación de despido, reenganches y procedimientos laborales prioritarios.
2. **`INSP` — Casos de Inspectoría / Horas Extra / Reclamos**:
   - *Dominio*: Administración de reclamaciones salariales, cálculo y pago de horas extra, bonificaciones y expedientes derivados de inspecciones laborales.
3. **`OFIC` — Expedientes en Oficina Consultoría Jurídica**:
   - *Dominio*: Agrupación de dictámenes jurídicos, consultas institucionales, opiniones legales y expedientes generales de la consultoría jurídica interna.
4. **`CONT` — Contrataciones y Convenios de la Universidad**:
   - *Dominio*: Registro de convenios interinstitucionales, contratos colectivos, instituciones aliadas, duración, tipos de convenio y fechas de vencimiento.
5. **`LITI` — Litigios Judiciales y Administrativos**:
   - *Dominio*: Control de demandas judiciales o administrativas, juzgados/tribunales asociados (`Tribunal`), fechas de demanda, tipos de demanda y abocamiento de abogados de la contraparte (`LitigiosContraparte`).
6. **`SUST` — Sustanciación de Procedimientos Disciplinarios**:
   - *Dominio*: Administración de expedientes sancionatorios al personal. Incluye cronómetros límite, horas, lugares y seguimiento detallado por **fases procesales**: *Auto de Inicio* (`INICIO`), *Periodo Probatorio* (`PRUEBAS`) y *Conclusiones / Dictamen* (`CONCL`).
7. **`IND` — Índices de Inspectoría del Trabajo**:
   - *Dominio*: Archivo y control de índices, estadísticas y expedientes catalogados bajo normativas formales de inspectoría.

---

## 🛠️ Tecnologías y Dependencias Principales

| Categoría | Tecnología / Librería | Propósito |
|---|---|---|
| **Core** | Python 3.11+ / Django 5.2 | Framework web y lógica de negocio |
| **API** | Django REST Framework (DRF) | Exposición de servicios RESTful |
| **Base de Datos** | MySQL 8.0 (`mysqlclient`) | Almacenamiento relacional e índice Fulltext |
| **Contenedores** | Docker & Docker Compose | Orquestación y despliegue estandarizado |
| **Criptografía** | `cryptography` (Fernet) | Cifrado de archivos at-rest |
| **Seguridad 2FA** | `django-otp` / `PyOTP` | Autenticación de doble factor TOTP |
| **Documentos Word** | `python-docx` | Generación y manipulación de plantillas `.docx` |
| **Documentos PDF** | `reportlab` / `pypdf` | Creación de PDFs y marcas de agua dinámicas |
| **OCR & Imágenes** | `pytesseract` / `Pillow` | Extracción de texto y procesamiento de imágenes |
| **Frontend** | Bootstrap 5 / JavaScript | Interfaz de usuario responsiva y moderna |

---




### 🐳 C. Despliegue con Docker (Linux & Windows)

El sistema incluye soporte completo para **Docker** y **Docker Compose**, permitiendo levantar el servicio de MySQL 8.0 y el contenedor de Django (Gunicorn) de forma totalmente aislada.

#### 📋 Paso 1: Configurar el archivo `.env` para Docker
Crea el archivo `.env` en la raíz del proyecto. *Nota: Para Docker Compose, el `DB_HOST` debe apuntar al nombre del servicio de la base de datos (`db`)*:
```env
DEBUG=True
SECRET_KEY=tu_secret_key_aleatoria_muy_segura
DATABASE_URL=tu url
DB_NAME=db_name
DB_USER=tu usuario
DB_PASSWORD=tu_contraseña_segura
DB_HOST=db
DB_PORT=3306
FERNET_KEY=tu_clave_fernet_generada_para_cifrado
```

---

#### 🐧 Paso 2A: Despliegue con Docker en Linux (Ubuntu / Debian / CentOS)

1. **Instalar Docker y Docker Compose:**
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose-v2
   sudo usermod -aG docker $USER
   ```
   *(Cierra sesión y vuelve a entrar si es necesario para aplicar los permisos de grupo).*

2. **Construir y levantar los contenedores:**
   ```bash
   docker compose up --build -d
   ```
   *(Docker ejecutará automáticamente las migraciones, la recolección de estáticos y levantará Gunicorn).*

3. **Verificar estado de los contenedores:**
   ```bash
   docker compose ps
   ```

4. **Crear superusuario (opcional):**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

---

#### 🪟 Paso 2B: Despliegue con Docker en Windows (Windows 10 / 11)

1. **Instalar Docker Desktop para Windows:**
   - Descarga e instala [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/).
   - Asegúrate de tener habilitado **WSL 2** (Windows Subsystem for Linux) cuando el instalador lo requiera.
   - Abre **Docker Desktop** y espera a que el icono de la barra de tareas indique que el motor está corriendo (*Engine running*).

2. **Abrir la terminal (PowerShell o CMD):**
   Navega hasta la carpeta raíz del proyecto SGEJ:
   ```cmd
   cd C:\ruta\a\SGEJ
   ```

3. **Construir y levantar los contenedores:**
   ```cmd
   docker compose up --build -d
   ```
   *(El contenedor `db` inicializará MySQL y el contenedor `web` aplicará las migraciones y levantará Gunicorn en segundo plano).*

4. **Verificar estado de los contenedores:**
   ```cmd
   docker compose ps
   ```

5. **Crear superusuario dentro del contenedor (opcional):**
   ```cmd
   docker compose exec web python manage.py createsuperuser
   ```

---

### 🌐 Acceso a la Aplicación
Independientemente de si estás en Linux o Windows usando Docker, abre tu navegador web e ingresa a:
👉 `http://localhost:8000`
