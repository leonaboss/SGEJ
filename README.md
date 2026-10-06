# ⚖️ SGEJ — Sistema de Gestor de Expedientes Jurídicos
Arquitectura Modular del Software y Requerimientos  
**Stack Tecnológico:** Django 5.2 + DRF + MySQL 8.0 + Bootstrap 5 + Criptografía AES/Fernet + Docker

---

## 🌟 Descripción General & Filosofía del Sistema

El **SGEJ (Sistema de Gestor de Expedientes Jurídicos)** es una obra maestra de ingeniería de software monolítica modular desarrollada bajo estrictos principios de **Domain-Driven Design (DDD)**. Es una plataforma robusta, elegante y de altísimo rendimiento diseñada para automatizar, blindar y simplificar el ciclo de vida completo de la gestión jurídica institucional, universitaria o corporativa. 

Desde la recepción automatizada de expedientes y la sustanciación de procedimientos disciplinarios hasta el cifrado forense de documentos at-rest, la firma digital con códigos QR y la auditoría inmutable en tiempo real, el SGEJ ofrece una experiencia de usuario impecable combinada con los más altos estándares arquitectónicos del desarrollo moderno. ¡Deleítate explorando un software diseñado para trascender!

---

## 🛡️ Seguridad Avanzada y Cumplimiento (OWASP Top 10)

El **SGEJ** ha sido construido bajo ciberseguridad defensiva de nivel empresarial, alineándose con las directrices **OWASP Top 10** y aplicando mitigaciones avanzadas a nivel de aplicación e infraestructura:

- **Cifrado Criptográfico At-Rest (AES / Fernet)**: Todos los documentos y archivos binarios confidenciales son cifrados antes de almacenarse en disco, impidiendo el acceso no autorizado sin la clave de cifrado institucional.
- **Bitácora de Auditoría Inmutable (SHA-256 Chained)**: Registro forense inalterable de todas las operaciones del sistema, protegido por middleware que bloquea estrictamente cualquier instrucción `UPDATE` o `DELETE` a nivel de base de datos.
- **Autenticación de Doble Factor (2FA / TOTP)**: Integración nativa con generadores de códigos temporales (Google Authenticator, FreeOTP) para cuentas privilegiadas.
- **Gestión de Identidad y RBAC Estricto**: Control de acceso basado en roles (`ADMIN`, `ABOG`, `USR_PUBLICO`) con aislamiento absoluto de datos mediante `BaseQuerySet`.
- **Protección contra Fuerza Bruta y Ataques**: Bloqueo automático de cuentas tras múltiples intentos fallidos de inicio de sesión, control de concurrencia de sesiones (`SessionControlMiddleware`) y límites de peticiones (`RateLimiting`).
- **Sistema Honeypot de Intrusos**: Trampas virtuales integradas en rutas críticas para identificar y registrar accesos maliciosos o sondeos automatizados.
- **Seguridad de Credenciales**: Hashing con `Argon2` / `PBKDF2` e historial inmutable de contraseñas que impide la reutilización de las últimas 3 claves.

---

## ⚙️ Arquitectura de Módulos del Sistema (Explicación Funcional)

El sistema está estructurado en 5 grandes aplicaciones (módulos) independientes y cohesivas:

### 1. Módulo de Autenticación, Usuarios y Seguridad (`apps/usuarios`)
- **¿Qué hace?**: Administra el ciclo de vida de los usuarios del sistema, control de acceso basado en roles (RBAC: `ADMIN`, `ABOG`, `USR_PUBLICO`), autenticación de doble factor (2FA/TOTP), preguntas de seguridad para recuperación, historial inmutable de contraseñas y la bitácora de auditoría inmutable con hashes encadenados.

### 2. Módulo del Núcleo Jurídico y Expedientes (`apps/expedientes`)
- **¿Qué hace?**: Es el motor principal del negocio jurídico. Gestiona los expedientes principales, directorios de personal, cargos institucionales, motivos de reclamo, tribunales y la agenda de audiencias con alertas automatizadas. Además, centraliza el directorio de **Sujetos Procesales** (Defensores, Fiscales, Jueces, Secretarios y Contrapartes).

### 3. Módulo de Gestión Documental y Cifrado (`apps/documentos`)
- **¿Qué hace?**: Controla la subida, almacenamiento seguro y cifrado en disco (AES/Fernet) de todos los archivos y documentos. Valida la integridad mediante hashes SHA-256 en cada descarga, administra firmas digitales, códigos QR de autenticidad, plantillas Word (`.docx`) para generación automatizada de escritos, búsqueda Full-Text con OCR (Tesseract) y marcas de agua dinámicas en PDFs.

### 4. Módulo de Biblioteca Legal y Normativa (`apps/biblioteca`)
- **¿Qué hace?**: Funciona como un repositorio institucional centralizado para almacenar y consultar normativas, reglamentos internos, resoluciones de consejo universitario y gacetas oficiales vinculables directamente a los expedientes.

### 5. Módulo de Infraestructura y Middleware (`apps/infraestructura`)
- **¿Qué hace?**: Provee los servicios transversales de seguridad defensiva, control de límites de peticiones (Rate Limiting), control de sesiones concurrentes y el sistema trampa (Honeypot) para detección de intrusos.

---

## 📂 Submódulos y Tipos de Módulos de Expedientes (`tipo_modulo`)

El núcleo de expedientes (`apps/expedientes`) clasifica la operatividad legal en **7 submódulos especializados**, cada uno con campos y flujos específicos:

1. **`DESP` — Calificación de Despido / Casos Recientes**:
   - *¿Qué hace?*: Gestiona expedientes urgentes relativos a solicitudes de calificación de despido, reenganches y procedimientos laborales prioritarios del personal.
2. **`INSP` — Casos de Inspectoría / Horas Extra / Reclamos**:
   - *¿Qué hace?*: Administra reclamaciones salariales, cálculo y pago de horas extra, bonificaciones y expedientes derivados de inspecciones laborales.
3. **`OFIC` — Expedientes en Oficina Consultoría Jurídica**:
   - *¿Qué hace?*: Agrupa dictámenes jurídicos, consultas institucionales, opiniones legales y expedientes generales tramitados por la consultoría jurídica interna.
4. **`CONT` — Contrataciones y Convenios de la Universidad**:
   - *¿Qué hace?*: Registra convenios interinstitucionales, contratos colectivos, instituciones aliadas, duración, tipos de convenio y fechas de vencimiento.
5. **`LITI` — Litigios Judiciales y Administrativos**:
   - *¿Qué hace?*: Controla demandas judiciales o administrativas, juzgados/tribunales asociados (`Tribunal`), fechas de demanda, tipos de demanda y abocamiento de los abogados de la contraparte (`LitigiosContraparte`).
6. **`SUST` — Sustanciación de Procedimientos Disciplinarios**:
   - *¿Qué hace?*: Administra expedientes sancionatorios o disciplinarios al personal. Incluye cronómetros límite, horas, lugares del procedimiento y seguimiento detallado por **fases procesales**: *Auto de Inicio* (`INICIO`), *Periodo Probatorio* (`PRUEBAS`) y *Conclusiones / Dictamen* (`CONCL`).
7. **`IND` — Índices de Inspectoría del Trabajo**:
   - *¿Qué hace?*: Archivo y control de índices, estadísticas y expedientes catalogados bajo normativas e índices formales de inspectoría.

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
