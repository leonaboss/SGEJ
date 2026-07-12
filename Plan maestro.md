PLAN DE DESARROLLO: Sistema de Gestor de expedientes juridicos(SGEJ)
1. Visión General
Sistema centralizado de automatización y auditoría para Consultoría Jurídica.

Arquitectura: Monolito modular con separación estricta de dominios (Domain-Driven Design).

Backend: Python 3.11 + Django (Framework) + Django Rest Framework (API).

Frontend: Bootstrap 5 (Responsive).

Base de Datos: MySQL 8.0.

Infraestructura: Despliegue en VPS (Dokploy + Render/Aiven).

2. Estructura de Proyecto (Backend)

/sgej_juridico
├── .env                  # Variables de entorno (DB, SECRETS, SMTP, 2FA)
├── manage.py
├── core/                 # Configuración principal
├── apps/
│   ├── usuarios/         # Auth, RBAC, Perfil, Bitácora, 2FA
│   ├── expedientes/      # Módulos: Despido, Inspección, Litigios, Sustanciación
│   ├── documentos/       # Gestión de archivos, Cifrado, Firma, OCR, QRs
│   ├── biblioteca/       # Normativa, Reglamentos, Buscador Dinámico
│   └── infraestructura/  # Middleware de Seguridad, Signals de Auditoría
└── static/               # Assets de frontend

3. Implementación de Base de Datos y Modelos
El ORM debe reflejar fielmente el DDL proporcionado, utilizando los campos adecuados:

Seguridad At-Rest: Campos nombre_cifrado, iv_cifrado y hash_sha256 en la tabla documentos.

Trazabilidad: Uso de bitacora_auditoria con inmutabilidad (middleware que captura el request, usuario, IP y genera el hash de integridad antes de guardar).

Relaciones: Configuración de on_delete=models.PROTECT para asegurar la integridad referencial.

4. Estrategia de Seguridad (OWASP & Compliance)
Capa de Autenticación
2FA: Integración obligatoria con django-otp para códigos TOTP.

Sesiones: Middleware de session_control para detectar inicios de sesión concurrentes y bloquear la sesión anterior.

Passwords: Hasheo con Argon2 o Bcrypt; implementación de historial de contraseñas mediante signals (cada cambio guarda en historial_contrasenas).

Capa de Cifrado
En Tránsito: Forzar HTTPS/TLS.

En Reposo: Implementar servicio en services.py que utilice cryptography.fernet para cifrar archivos antes de su almacenamiento físico.

Capa de Auditoría e Integridad
Inmutabilidad: La bitacora_auditoria no permite actualizaciones (update) ni eliminaciones (delete) a nivel de aplicación. Solo inserciones.

Honeypot: Inserción de registros trampa en la bitácora para detectar intentos de inyección o manipulación no autorizada.

5. Requerimientos Funcionales y Módulos
Tableros: Cards dinámicas en el Dashboard que consultan la base de datos (con índices optimizados) para mostrar conteos en tiempo real mediante caching ligero.

Documentos:

Generación automática de documentos desde plantillas (renderizado de Word/PDF).

Visor interno para evitar descargas.

Marcado de agua dinámico (Cédula + Fecha) al renderizar PDFs.

QR: Generación de QR único por expediente con validación de rol para acceso.

Personal: Clasificación estricta (DOC, ADM, OBR) y vinculación a marcos legales (Ley del Trabajo vs Reglamento).

6. Instrumento de Validación (Project Manager Checklist)
El sistema debe cumplir con:

Performance: Lighthouse > 90, LCP < 7s.

UX/UI: Diseño homogéneo, mensajes de ayuda, responsividad total (Bootstrap).

Seguridad (Crítico):

Validación W3C.

Bloqueo a los 3 intentos fallidos.

RBAC (Role Based Access Control) estricto.

Sanitización estricta de subidas de archivos (validación de extensiones y renombramiento).

Uso de CSRF Tokens, CORS, Httponly Cookies.

7. Instrucciones para el IDE (Google Antigravity)
Configuración Inicial: Conectar con MySQL mediante variables en .env (no codificar credenciales en settings.py).

Principios SOLID:

Single Responsibility: Cada módulo de la App debe manejar su propia lógica de negocio.

Dependency Inversion: Usar services.py para inyectar lógica de cifrado y auditoría.

Mantenibilidad: Crear migraciones limpias y ejecutar makemigrations tras definir modelos.

Respaldo: Implementar script de Python que exporte diariamente la base de datos a SQL, PDF y Excel (usando openpyxl).

Instrucciones de uso:
Copia este contenido en un archivo .md.

Asegúrate de tener instalado Python 3.11, Django, mysql-connector-python y cryptography.

Al inicializar, el IDE debe configurar primero el CustomUserModel y el Middleware de auditoría antes de cualquier otra entidad para garantizar que el log de eventos funcione desde el primer registro.

2.2 Aplicación: expedientes (Modelos del Núcleo de Negocio)

from django.db import models

class Personal(models.Model):
    numero_expediente = models.CharField(max_length=50, blank=True, null=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(max_length=150, unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personal'


class Cargo(models.Model):
    CATEGORIAS = [('DOC', 'Docente'), ('ADM', 'Administrativo'), ('OBR', 'Obrero')]
    TIPOS = [('FIJ', 'Fijo / Carrera'), ('CON', 'Contratado'), ('CAR', 'Libre Nombramiento y Remoción')]
    
    categoria = models.CharField(max_length=3, choices=CATEGORIAS)
    tipo = models.CharField(max_length=3, choices=TIPOS)
    marco_legal = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cargos'
        unique_together = ('categoria', 'tipo')


class PersonaCargo(models.Model):
    personal = models.ForeignKey(Personal, on_delete=models.PROTECT, db_column='personal_id')
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, db_column='cargo_id')
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    es_cargo_actual = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'persona_cargo'


class Motivo(models.Model):
    descripcion = models.TextField()
    tipo = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'motivos'


class Tribunal(models.Model):
    TIPOS = [('CONT', 'Contencioso'), ('INSP', 'Inspectoría del Trabajo'), ('OTRO', 'Otros')]
    nombre = models.CharField(max_length=150, unique=True)
    tipo = models.CharField(max_length=4, choices=TIPOS)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tribunales'


class Expediente(models.Model):
    MODULOS = [
        ('DESP', 'Calificación de Despido / Recientes'),
        ('INSP', 'Casos de Inspectoría / Horas Extra / Reclamos'),
        ('OFIC', 'Expedientes en Oficina Consultoría Jurídica'),
        ('CONT', 'Contrataciones y Convenios de la Universidad'),
        ('LITI', 'Litigios Judiciales y Administrativos'),
        ('SUST', 'Sustanciación de Procedimientos Disciplinarios'),
        ('IND', 'Índices de Inspectoría del Trabajo')
    ]
    TEMAS = [('LAB', 'Laboral'), ('ADM', 'Administrativo'), ('ACA', 'Académico')]
    FASES = [('INICIO', 'Auto de Inicio'), ('PRUEBAS', 'Periodo Probatorio'), ('CONCL', 'Conclusiones / Dictamen')]

    numero_expediente = models.CharField(max_length=50, unique=True)
    numero_expediente_relativo = models.CharField(max_length=50, blank=True, null=True)
    tipo_modulo = models.CharField(max_length=4, choices=MODULOS)
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.PROTECT, db_column='usuario_id')
    personal = models.ForeignKey(Personal, on_delete=models.PROTECT, blank=True, null=True, db_column='personal_id')
    motivo = models.ForeignKey(Motivo, on_delete=models.PROTECT, blank=True, null=True, db_column='motivo_id')
    estatus = models.CharField(max_length=50, blank=True, null=True)
    fecha_registro = models.DateField(blank=True, null=True)
    tema_filtro = models.CharField(max_length=3, choices=TEMAS, blank=True, null=True)
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, blank=True, null=True, db_column='cargo_id')
    institucion = models.CharField(max_length=200, blank=True, null=True)
    ano = models.IntegerField(blank=True, null=True)
    duracion = models.CharField(max_length=100, blank=True, null=True)
    tipo_convenio = models.TextField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    tipo_demanda = models.CharField(max_length=150, blank=True, null=True)
    tribunal = models.ForeignKey(Tribunal, on_delete=models.PROTECT, blank=True, null=True, db_column='tribunal_id')
    hora_procedimiento = models.TimeField(blank=True, null=True)
    lugar_procedimiento = models.CharField(max_length=255, blank=True, null=True)
    fase_actual = models.CharField(max_length=7, choices=FASES, blank=True, null=True)
    cronometro_limite = models.DateTimeField(blank=True, null=True)
    documentos_procesados = models.IntegerField(default=0)
    correspondencia_recibida = models.IntegerField(default=0)
    correspondencia_enviada = models.IntegerField(default=0)
    is_archivado = models.BooleanField(default=False, db_column='is_archivado')
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'expedientes'


class Actuacion(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.PROTECT, db_column='expediente_id')
    descripcion = models.TextField()
    documento = models.ForeignKey('Documento', on_delete=models.PROTECT, blank=True, null=True, db_column='documento_id')
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.PROTECT, db_column='usuario_id')
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'actuaciones'


class ModuloBiblioteca(models.Model):
    TIPOS = [('REGL', 'Reglamento Interno'), ('RESCU', 'Resolución de Consejo Universitario'), ('GAC', 'Gaceta Oficial')]
    titulo = models.CharField(max_length=255)
    tipo_normativa = models.CharField(max_length=5, choices=TIPOS)
    fecha_publicacion = models.DateField()
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'modulo_biblioteca'


class Documento(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.PROTECT, blank=True, null=True, db_column='expediente_id')
    biblioteca = models.ForeignKey(ModuloBiblioteca, on_delete=models.PROTECT, blank=True, null=True, db_column='biblioteca_id')
    nombre_original = models.CharField(max_length=255)
    nombre_cifrado = models.CharField(max_length=255)
    tipo_mime = models.CharField(max_length=100)
    hash_sha256 = models.CharField(max_length=64)
    iv_cifrado = models.CharField(max_length=64)
    qr_code_content = models.CharField(max_length=500, unique=True, blank=True, null=True)
    contenido_ocr = models.TextField(blank=True, null=True)
    version = models.IntegerField(default=1)
    parent_documento = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True, db_column='parent_documento_id')
    normativa_citada = models.ForeignKey(ModuloBiblioteca, on_delete=models.PROTECT, blank=True, null=True, related_name='citado_en_documentos', db_column='normativa_citada_id')
    es_plantilla = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('usuarios.Usuario', on_delete=models.PROTECT, db_column='created_by')

    class Meta:
        db_table = 'documentos'


class DocumentoFirma(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.PROTECT, db_column='documento_id')
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.PROTECT, db_column='usuario_id')
    hash_firma = models.CharField(max_length=64)
    sello_digital_path = models.CharField(max_length=255, blank=True, null=True)
    fecha_firma = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'documentos_firmas'
        unique_together = ('documento', 'usuario')


class AudienciaAgenda(models.Model):
    EVENTOS = [('AUD', 'Audiencia Judicial'), ('LAPS', 'Lapso Procesal'), ('VENC', 'Vencimiento Contrato'), ('REC', 'Recordatorio General')]
    expediente = models.ForeignKey(Expediente, on_delete=models.PROTECT, db_column='expediente_id')
    titulo = models.CharField(max_length=200)
    tipo_evento = models.CharField(max_length=4, choices=EVENTOS)
    fecha_hora = models.DateTimeField()
    descripcion = models.TextField(blank=True, null=True)
    notificado_30 = models.BooleanField(default=False)
    notificado_60 = models.BooleanField(default=False)
    notificado_90 = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audiencias_agenda'


class LitigioContraparte(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.PROTECT, db_column='expediente_id')
    nombre_abogado = models.CharField(max_length=150)
    datos_contacto = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'litigios_contrapartes'


class Notificacion(models.Model):
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.PROTECT, db_column='usuario_id')
    mensaje = models.TextField()
    tipo_alerta = models.CharField(max_length=50)
    leido = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificaciones'


class SustanciacionNotificacion(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.PROTECT, db_column='expediente_id')
    personal = models.ForeignKey(Personal, on_delete=models.PROTECT, db_column='personal_id')
    fecha = models.DateField()
    hora = models.TimeField()
    lugar = models.CharField(max_length=255)
    firma_digital_path = models.CharField(max_length=255, blank=True, null=True)
    huella_digital_hash = models.CharField(max_length=64, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sustanciacion_notificaciones'

3. LÓGICA DE BACKEND ESPECIALIZADA (ARQUITECTURA COMPLETA)
3.1 Flujo de Autenticación, Bloqueos e Historial de Contraseñas
El sistema implementa una política robusta que no permite reutilizar ninguna de las últimas 3 contraseñas, bloquea la cuenta al tercer intento fallido y soporta un doble factor de autenticación híbrido.

Django Signal para Historial Obligatorio de Contraseñas (signals.py):
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
from apps.usuarios.models import Usuario, HistorialContrasena
import re

@receiver(pre_save, sender=Usuario)
def verificar_politica_y_guardar_historial(sender, instance, **kwargs):
    if instance.id:
        usuario_db = Usuario.objects.get(id=instance.id)
        # Si la contraseña ha cambiado
        if usuario_db.password_hash != instance.password_hash:
            # Validar longitud mínima de 16 caracteres
            # Nota: Si viene ya encriptada por el framework se valida en el formulario de origen
            
            # Verificar histórico de las últimas 3 contraseñas
            historial = HistorialContrasena.objects.filter(usuario=instance).order_range('-created_at')[:3]
            from django.contrib.auth.hashers import check_password
            for h in historial:
                if check_password(instance._password_plana_temporal, h.password_hash):
                    raise ValueError("No puedes reutilizar ninguna de tus últimas 3 contraseñas.")
            
            # Guardar la contraseña saliente en la tabla de historial
            HistorialContrasena.objects.create(
                usuario=instance,
                password_hash=usuario_db.password_hash
            )

Flujo de Recuperación de Contraseña Variable (Entorno Dependiente):
En los endpoints de recuperación, se lee la variable de entorno ENTORNO:

Si ENTORNO == 'produccion' (Dominio): Se genera un token de seguridad firmado único y se envía un enlace de restablecimiento dinámico vía correo electrónico institucional.

Si ENTORNO == 'localhost' (Comunidad local sin Internet): El sistema activa el método por Frase de Seguridad. El usuario debe ingresar la combinación exacta de su Cédula, Nombre de Usuario y responder correctamente la pregunta basada en la FRASE_SEGURIDAD_MAESTRA configurada en el servidor para permitir el bypass transaccional validado por el Administrador.

3.2 Capa de Auditoría Inmutable (Middleware)
Se intercepta de forma asíncrona cada petición transaccional destructiva o de lectura crítica y se escribe en bitacora_auditoria. Ninguna instrucción UPDATE o DELETE está permitida sobre esta tabla.

import hashlib
from django.utils.deprecation import MiddlewareMixin
from apps.expedientes.models import BitacoraAuditoria

class AuditoriaInmutableMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method in ['POST', 'PUT', 'DELETE'] or 'login' in request.path:
            request._audit_tracked = True

    def process_response(self, request, response):
        if getattr(request, '_audit_tracked', False) and response.status_code in [200, 201, 302]:
            usuario = request.user if request.user.is_authenticated else None
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '0.0.0.0')).split(',')[0].strip()
            
            actuacion = request.method
            if 'login' in request.path:
                actuacion = "LOGIN_INTENT"
            
            modulo = request.path.split('/')[2] if len(request.path.split('/')) > 2 else 'CORE'
            descripcion = f"Usuario ejecutó {request.method} en la ruta {request.path} con código de respuesta {response.status_code}"
            
            # Obtener el último hash de la base de datos para encadenamiento estructural (Inmutabilidad Estilo Blockchain)
            ultimo_log = BitacoraAuditoria.objects.all().order_by('-id').first()
            prev_hash = ultimo_log.hash_integridad if ultimo_log else "GENESIS_HASH"
            
            # Generar Hash SHA-256 de integridad combinando datos actuales y el hash anterior
            raw_string = f"{prev_hash}|{usuario.id if usuario else 'ANON'}|{actuacion}|{modulo}|{ip}|{descripcion}"
            hash_integridad = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
            
            # Persistir de forma directa
            BitacoraAuditoria.objects.create(
                usuario=usuario,
                actuacion=actuacion,
                descripcion=descripcion,
                modulo=modulo,
                ip_address=ip,
                hash_integridad=hash_integridad
            )
        return response

3.3 Gestión de Documentos y Cifrado At-Rest (services.py)
Los expedientes legales contienen información institucional sensible de la universidad. Los archivos PDF y fotos no deben guardarse planos en el disco del servidor.

import os
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings
from apps.expedientes.models import Documento
import qrcode

class DocumentoSecurizadoService:
    @staticmethod
    def procesar_y_cifrar_archivo(archivo_plano, expediente_obj, usuario_creador):
        # 1. Calcular Hash SHA-256 de Integridad del archivo original
        sha256_context = hashlib.sha256()
        for chunk in archivo_plano.chunks():
            sha256_context.update(chunk)
        hash_sha256 = sha256_context.hexdigest()
        
        # 2. Inicializar Cifrado Simétrico (AES-256 a través de Fernet compatible)
        # La clave secreta de cifrado físico se genera de forma única en el despliegue
        key = Fernet.generate_key() # En implementación real se lee de llave maestra externa
        fernet = Fernet(key)
        
        contenido_binario = archivo_plano.read()
        contenido_cifrado = fernet.encrypt(contenido_binario)
        
        # 3. Guardar físicamente el archivo encriptado en disco
        nombre_original = archivo_plano.name
        nombre_cifrado_uuid = f"{hash_sha256}.enc"
        ruta_destino = os.path.join(settings.MEDIA_ROOT, 'securized_docs', nombre_cifrado_uuid)
        
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
        with open(ruta_destino, 'wb') as f:
            f.write(contenido_cifrado)
            
        # 4. Generación Automática Obligatoria de Código QR Unificado
        qr_data = f"SGIJ-EXPEDIENTE:{expediente_obj.numero_expediente}|HASH:{hash_sha256}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        qr_filename = f"QR_{hash_sha256}.png"
        qr_path = os.path.join(settings.MEDIA_ROOT, 'qrs', qr_filename)
        os.makedirs(os.path.dirname(qr_path), exist_ok=True)
        img_qr.save(qr_path)
        
        # 5. Registrar metadatos completos en la base de datos MySQL
        documento_instancia = Documento.objects.create(
            expediente=expediente_obj,
            nombre_original=nombre_original,
            nombre_cifrado=nombre_cifrado_uuid,
            tipo_mime=archivo_plano.content_type,
            hash_sha256=hash_sha256,
            iv_cifrado=key.decode('utf-8'), # Se almacena la llave/iv encapsulada bajo estricto control
            qr_code_content=qr_data,
            version=1,
            created_by=usuario_creador
        )
        
        return documento_instancia

3.4 Serializadores de la Capa de API Anidada (serializers.py)
Permite obtener toda la trazabilidad y árbol documental de un expediente judicial en una sola llamada GET, optimizando drásticamente el performance.

from rest_framework import serializers
from apps.expedientes.models import Expediente, Actuacion, Documento

class DocumentoAnidadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = ['id', 'nombre_original', 'hash_sha256', 'qr_code_content', 'version', 'created_at']


class ActuacionAnidadaSerializer(serializers.ModelSerializer):
    documento = DocumentoAnidadoSerializer(read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.usuario', read_only=True)

    class Meta:
        model = Actuacion
        fields = ['id', 'descripcion', 'documento', 'usuario_nombre', 'created_at']


class ExpedienteDetalleCompletoSerializer(serializers.ModelSerializer):
    actuaciones = ActuacionAnidadaSerializer(source='actuacion_set', many=True, read_only=True)
    documentos = DocumentoAnidadoSerializer(source='documento_set', many=True, read_only=True)
    personal_cedula = serializers.CharField(source='personal.cedula', read_only=True)
    personal_nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Expediente
        fields = [
            'id', 'numero_expediente', 'numero_expediente_relativo', 'tipo_modulo', 
            'estatus', 'fecha_registro', 'tema_filtro', 'personal_cedula', 
            'personal_nombre_completo', 'is_archivado', 'actuaciones', 'documentos'
        ]

    def get_personal_nombre_completo(self, obj):
        if obj.personal:
            return f"{obj.personal.nombres} {obj.personal.apellidos}"
        return "No Asignado"

4. DISEÑO DE INTERFAZ HOMOGÉNEA Y FRONTEND (BOOTSTRAP 5)La interfaz se estructura bajo un diseño responsivo unificado, garantizando un flujo fluido, navegación asistida y modales explícitos de confirmación para salvaguardar la integridad de las acciones operativas.


4.1 Módulos y Columnas de Visualización de Tablas RequeridasCada módulo mapea directamente un subconjunto de datos filtrados por la columna tipo_modulo en la tabla maestra expedientes.Módulo de Casos de Trabajo Recientes / Calificación de Despido (tipo_modulo == 'DESP')Columnas de Tabla: N° de Expediente, Nombre y Apellido, Cédula, Motivo, Estatus.Funciones Especiales: Asignación correlativa basada en marca temporal con opción de edición por el abogado, visor PDF incrustado con marca de agua dinámica, tablero Kanban/Lista de estatus de colores (Recibido=Gris, En Análisis=Azul, Firma=Amarillo, Despachado=Verde).Módulo de Casos de Inspectoría del Trabajo / Reclamo de Horas Extra (tipo_modulo == 'INSP')Columnas de Tabla: N° de Expediente, Nombre y Apellido, Cédula, Motivo, Fecha.Módulo de Expedientes en Oficina de Consultoría Jurídica (tipo_modulo == 'OFIC')Columnas de Tabla: N° de Expediente, Nombre y Apellido, Cédula, Cargo, Estatus.Módulo de Contrataciones y Convenios de la Universidad (tipo_modulo == 'CONT')Columnas de Tabla: Institución, Año, Duración, Tipo de Convenio (Descripción), Fecha de Vencimiento.Funciones Especiales: Repositorio de plantillas base, historial inmutable de versiones del borrador legal y alertas automatizadas a los 30, 60 y 90 días del vencimiento absoluto.Módulo de Litigios (tipo_modulo == 'LITI')Columnas de Tabla: Tipo de Demanda, Fecha de Demanda, Estatus, Tribunal.Funciones Especiales: Gestión de abogados de la contraparte y agenda unificada con alertas automáticas.Módulo de Sustanciación de Procedimientos Disciplinarios (tipo_modulo == 'SUST')Funciones Especiales: Flujograma visual interactivo de los lapsos del procedimiento administrativo ordinario (Auto de Inicio $\rightarrow$ Período Probatorio $\rightarrow$ Conclusiones), automatización de boletas y cronómetro de perención legal en tiempo real.Tabla Secundaria de Notificaciones Relacionada: Nombres y Apellidos, Cédula, Fecha, Hora, Lugar, Firma y Huella Digital.Módulo de Índices de Inspectoría del Trabajo (tipo_modulo == 'IND')Columnas de Tabla: Nombres y Apellidos, Cédula, Expediente, Motivo.


4.2 Maquetación del Dashboard y Conteo Dinámico (Cards)
El panel principal presenta un layout de rejilla responsiva que consume asíncronamente el conteo total de expedientes activos por categoría. Cada vez que un registro cambia de estado o pasa a is_archivado = 1, los contadores disminuyen e incrementan en consecuencia de forma reactiva.

<div class="container-fluid py-4 bg-light">
    <div class="row row-cols-1 row-cols-md-3 row-cols-xl-4 g-4 mb-4">
        
        <div class="col">
            <div class="card h-100 border-0 shadow-sm bg-white">
                <div class="card-body d-flex align-items-center justify-content-between">
                    <div>
                        <h6 class="text-muted text-uppercase small mb-1">Calificación de Despido</h6>
                        <h2 class="fw-bold mb-0 text-dark" id="count-despido">0</h2>
                    </div>
                    <div class="badge bg-secondary p-3"><i class="bi bi-person-x-fill fs-4"></i></div>
                </div>
            </div>
        </div>

        <div class="col">
            <div class="card h-100 border-0 shadow-sm bg-white">
                <div class="card-body d-flex align-items-center justify-content-between">
                    <div>
                        <h6 class="text-muted text-uppercase small mb-1">Casos Inspectoría</h6>
                        <h2 class="fw-bold mb-0 text-dark" id="count-inspectoría">0</h2>
                    </div>
                    <div class="badge bg-primary p-3"><i class="bi bi-briefcase-fill fs-4"></i></div>
                </div>
            </div>
        </div>

        <div class="col">
            <div class="card h-100 border-0 shadow-sm bg-white">
                <div class="card-body d-flex align-items-center justify-content-between">
                    <div>
                        <h6 class="text-muted text-uppercase small mb-1">En Oficina Jurídica</h6>
                        <h2 class="fw-bold mb-0 text-dark" id="count-oficina">0</h2>
                    </div>
                    <div class="badge bg-info p-3"><i class="bi bi-folder-fill fs-4"></i></div>
                </div>
            </div>
        </div>

        <div class="col">
            <div class="card h-100 border-0 shadow-sm bg-white">
                <div class="card-body d-flex align-items-center justify-content-between">
                    <div>
                        <h6 class="text-muted text-uppercase small mb-1">Convenios UPTAG</h6>
                        <h2 class="fw-bold mb-0 text-dark" id="count-convenios">0</h2>
                    </div>
                    <div class="badge bg-success p-3"><i class="bi bi-journal-text fs-4"></i></div>
                </div>
            </div>
        </div>

        <div class="col">
            <div class="card h-100 border-0 shadow-sm bg-white">
                <div class="card-body d-flex align-items-center justify-content-between">
                    <div>
                        <h6 class="text-muted text-uppercase small mb-1">Litigios Activos</h6>
                        <h2 class="fw-bold mb-0 text-dark" id="count-litigios">0</h2>
                    </div>
                    <div class="badge bg-danger p-3"><i class="bi bi-gavel fs-4"></i></div>
                </div>
            </div>
        </div>

        <div class="col">
            <div class="card h-100 border-0 shadow-sm bg-white">
                <div class="card-body d-flex align-items-center justify-content-between">
                    <div>
                        <h6 class="text-muted text-uppercase small mb-1">Sustanciación Disciplinaria</h6>
                        <h2 class="fw-bold mb-0 text-dark" id="count-sustanciacion">0</h2>
                    </div>
                    <div class="badge bg-warning p-3"><i class="bi bi-shield-exclamation fs-4"></i></div>
                </div>
            </div>
        </div>

        <div class="col">
            <div class="card h-100 border-0 shadow-sm bg-white">
                <div class="card-body d-flex align-items-center justify-content-between">
                    <div>
                        <h6 class="text-muted text-uppercase small mb-1">Índices Inspectoría</h6>
                        <h2 class="fw-bold mb-0 text-dark" id="count-indices">0</h2>
                    </div>
                    <div class="badge bg-dark p-3"><i class="bi bi-list-check fs-4"></i></div>
                </div>
            </div>
        </div>

    </div>
</div>

4.3 Arquitectura de Control UX y Modales Críticos de Doble Confirmación
Cualquier interacción de guardado, actualización o borrado lógico debe activar de forma obligatoria un modal de control de interfaz de usuario. Ninguna petición viaja al servidor sin aprobación explícita en pantalla.

<div class="modal fade" id="modalConfirmacionSeguridad" data-bs-backdrop="static" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow">
            <div class="modal-header bg-dark text-white">
                <h5 class="modal-title"><i class="bi bi-shield-lock-fill me-2"></i>Confirmación de Seguridad Requerida</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body py-4">
                <p class="mb-3 text-muted">Para ejecutar cambios sobre el registro legal seleccionado, introduzca o confirme el nombre exacto de la entidad o archivo afectado para validar la consistencia:</p>
                <div class="mb-3">
                    <label class="form-label fw-bold small text-uppercase">Validación del Recurso:</label>
                    <input type="text" class="form-control" id="inputNombreValidacionArchivo" placeholder="Escriba el identificador o nombre del archivo para desbloquear">
                </div>
                <div class="alert alert-warning mb-0 small" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>Esta operación se registrará de forma irrevocable en la bitácora inmutable de auditoría del sistema con su dirección IP asociada.
                </div>
            </div>
            <div class="modal-footer bg-light">
                <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Abortar Acción</button>
                <button type="button" class="btn btn-danger" id="btnConfirmarAccionCritica">Ejecutar y Registrar Transacción</button>
            </div>
        </div>
    </div>
</div>

5. REQUERIMIENTOS NO FUNCIONALES Y MATRIZ DE VALIDACIÓN DE CALIDADEl desarrollo completo generado por el IDE Google Antigravity debe someterse a evaluación rigurosa bajo los siguientes parámetros de calidad de software estructurados por categorías exactas.

ID.  Categoría de Validación Criterio Técnico Exigido (Métricas de Ingeniería de Software)

1. Requerimiento de Validación Verificación absoluta de recolección de historias de usuario reflejada en modelos relacionales específicos.

2. Requerimiento de Validación Diseño del backend estructurado bajo patrón MVC/MVT limpio, robusto y desacoplado de dependencias pesadas.

3. UI / FrontendEstilo visual de la interfaz web homogéneo, utilizando paletas institucionales desaturadas a través de Bootstrap.

4. UI / FrontendOptimización del performance: Reporte de Google Lighthouse con puntuación estricta mayor a 90 puntos. Tiempo de carga del LCP (Largest Contentful Paint) controlado para no ser mayor a 7 segundos bajo conexiones restringidas.

5. UI / FrontendDiseño adaptativo / Responsivo fluido (Mobile-First) sin pérdida de legibilidad de las celdas de las tablas de expedientes.

6. UI / FrontendCumplimiento e integridad estricta de los estándares de marcado de la W3C.

7. UI / FrontendEl sistema proporciona mensajes contextuales nativos de ayuda al usuario ante errores de operación.

8. Eficiencia y FuncionalidadEl tiempo de respuesta de las APIs del servidor de base de datos MySQL debe ser óptimo (<200ms por consulta simple indexada).
 
9. Eficiencia y FuncionalidadArquitectura dimensionada correctamente para soportar las transacciones concurrentes sin fugas de memoria en hilos.

10. Eficiencia y FuncionalidadMantenibilidad absoluta de código: Cobertura de pruebas unitarias y aplicación estricta de Principios SOLID.

11. UsabilidadComprensión inmediata de flujos operativos sin necesidad de manuales externos de entrenamiento intensivo.

12. UsabilidadDiseño accesible considerando limitaciones motoras y perceptuales de los operadores legales de la oficina jurídica.

13. UsabilidadImplementación estricta de validadores en formularios (Regex para cédula, correo institucional, números telefónicos).

14. UsabilidadMantenimiento consistente del flujo de navegación sin quiebres de sesión inesperados al recargar páginas.

15. Seguridad IntegralAutenticación multi-capa: Contraseña robusta + Código de Verificación TOTP dinámico obligatorio. 

16. Seguridad IntegralResguardo absoluto de los expedientes digitales mediante algoritmos de cifrado simétrico verificados en servidor. 

17. Seguridad Integral Bloqueo automático del usuario tras ingresar la contraseña de forma errónea tres (3) veces consecutivas.

18. Seguridad IntegralLa acción de bloqueo y desbloqueo operativo de cuentas está restringida únicamente al rol de Administrador General.

19. Seguridad IntegralEl Administrador debe ingresar su segundo factor de autenticación activo para poder accionar la baja de un usuario. 

20. Seguridad IntegralAutorización controlada por Control de Acceso Basado en Roles (RBAC) interconectado con aislamiento completo de datos.

21. Seguridad IntegralDenegación automática implícita de accesos a rutas del sistema no explícitamente autorizadas en la matriz de roles.

22. Seguridad IntegralHasheo de contraseñas de una sola vía utilizando algoritmos robustos con sal criptográfica segura (Argon2ID/Bcrypt). 

23. Seguridad IntegralLongitud mínima de contraseñas configurada en 16 caracteres, sin límite máximo de almacenamiento físico.

24. Seguridad IntegralMecanismo adaptativo de recuperación de contraseña (enlace securizado en dominio / frase de seguridad en localhost).

25. Seguridad IntegralLa información confidencial o credenciales jamás se almacena en caché, almacenamiento local desprotegido o variables visibles.

26. Seguridad Integral Bitácora de auditoría transaccional inmutable (sólo inserción) con generación de hashes SHA-256 encadenados. 

27. Seguridad IntegralProtección activa del servidor web contra ataques de inyección mediante CSRF tokens, políticas CORS, cookies HttpOnly y Secure habilitadas en cabeceras TLS.

6. PROTOCOLOS DE SEGURIDAD AVANZADOS OWASP VINCULADOS

1. A02: Cryptographic Failures (Fallas Criptográficas): Implementación forzada de cifrado At-Rest para todo el almacenamiento de PDFs dentro del expediente digital único. Uso de firmas con Hash de Integridad SHA-256 para el no repudio de dictámenes jurídicos. Si un documento es alterado aunque sea en un solo bit en el sistema de archivos del servidor, la verificación del hash fallará de inmediato marcándolo en la interfaz como "Documento Corrupto / Firma Inválida".

2. A03: Injection (Inyecciones): Mitigación absoluta de Inyección SQL mediante el uso mandatorio del mapeador relacional de objetos de Django (Django ORM Prepared Statements). No está permitido bajo ninguna circunstancia concatenar cadenas crudas dentro de bloques .raw() o sentencias SQL directas.

3. Sanitización de Archivos y OCR: Cada documento PDF o imagen cargada se valida estrictamente verificando sus Magic Numbers (firma de encabezado de archivo real) y no solo la extensión textual. Se renombran los archivos utilizando UUIDs aleatorios al guardarlos para evitar la ejecución remota de scripts maliciosos. El motor OCR procesa el texto plano de forma aislada en un entorno de sandbox seguro.

4. Marcas de Agua Dinámicas en Visor Integrado: Al previsualizar cualquier PDF confidencial desde el navegador, un componente backend inyecta una marca de agua transparente sobre el lienzo del documento conteniendo la Cédula de Identidad del usuario activo y la marca temporal exacta de la consulta, mitigando la fuga de información sensible a través de fotografías de pantalla de dispositivos externos.

5. Offline First y Service Workers: Para garantizar resiliencia operativa ante fluctuaciones de conectividad en la comunidad local, se implementan Service Workers que cachean las estructuras de los formularios y tablas de expedientes. Toda transacción efectuada en modo local (Offline) se encola localmente de forma cifrada en IndexedDB y se sincroniza automáticamente mediante una cola de mutaciones con el backend en la nube en el instante exacto en que se restablezca el acceso a Internet.

7. DIRECTIVAS DE CONSTRUCCIÓN COMPLETA PARA EL IDE GOOGLE ANTIGRAVITY

El IDE Google Antigravity debe leer este documento de contexto y proceder con la generación del proyecto siguiendo secuencialmente las reglas estructuradas a continuación:

1. Regla de Inicialización: Crear el entorno virtual, instalar las dependencias especificadas y estructurar el árbol de directorios dividiendo la aplicación en los dominios aislados descritos en la Sección 2.

2. Regla de Base de Datos: Configurar la conexión nativa a la base de datos MySQL en el archivo settings.py apuntando a las variables de entorno del archivo .env, asegurando que use las credenciales root y clave 123456 proporcionadas para la fase de construcción inicial. Generar las migraciones limpias (makemigrations) y ejecutarlas (migrate).

3. Regla de Principios SOLID: Separar minuciosamente la lógica de negocio de las vistas de Django. Toda función de procesamiento complejo (generación de QR, cifrado AES, exportación de reportes Excel con openpyxl, marcas de agua) debe encapsularse dentro de clases de servicios puras en archivos services.py.

4. Regla de Interfaz de Usuario: Generar las plantillas HTML extendiendo de un componente base común base.html que cargue la versión estable de Bootstrap 5. Diseñar la barra lateral de navegación, el Dashboard dinámico interactivo con las cartas de conteo reactivo y asociar a cada botón operativo de edición o eliminación el modal de confirmación de seguridad correspondiente.

5. Regla de Cumplimiento de Calidad: Validar que cada endpoint verifique de forma estricta los permisos del usuario activo mediante decoradores o mixins basados en la tabla de Roles (RBAC), bloqueando de forma absoluta cualquier acceso no explícitamente parametrizado.

