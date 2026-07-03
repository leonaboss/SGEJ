from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.usuarios.models import Usuario
from apps.expedientes.models import Personal, Expediente
from apps.documentos.services import DocumentoSecurizadoService


class DocumentoSubidaTest(TestCase):
    def setUp(self):
        self.client = Client()
        personal_admin = Personal.objects.create(
            nombres='Admin', apellidos='Test', cedula='50000001'
        )
        self.admin = Usuario.objects.create_superuser(
            usuario='admin', password='Clave1234!!Segura',
            personal=personal_admin, cedula='50000001'
        )
        personal_exp = Personal.objects.create(
            nombres='Test', apellidos='User', cedula='99999999'
        )
        self.expediente = Expediente.objects.create(
            numero_expediente='DOC-TEST-001',
            tipo_modulo='DESP',
            personal=personal_exp,
            usuario=self.admin
        )
        self.client.login(usuario='admin', password='Clave1234!!Segura')

    def test_upload_form_accessible(self):
        response = self.client.get(reverse('documentos:documento_upload'))
        self.assertEqual(response.status_code, 200)

    def test_list_documentos(self):
        response = self.client.get(reverse('documentos:documento_list'))
        self.assertEqual(response.status_code, 200)


class DocumentoServiceTest(TestCase):
    def setUp(self):
        personal_admin = Personal.objects.create(
            nombres='Admin', apellidos='Test', cedula='60000001'
        )
        self.admin = Usuario.objects.create_superuser(
            usuario='admin', password='Clave1234!!Segura',
            personal=personal_admin, cedula='60000001'
        )
        personal_exp = Personal.objects.create(
            nombres='Test', apellidos='User', cedula='88888888'
        )
        self.expediente = Expediente.objects.create(
            numero_expediente='SRV-TEST-001',
            tipo_modulo='DESP',
            personal=personal_exp,
            usuario=self.admin
        )

    def test_cifrado_y_descifrado(self):
        archivo = SimpleUploadedFile(
            'test.pdf',
            b'Contenido del documento de prueba',
            content_type='application/pdf'
        )
        doc = DocumentoSecurizadoService.procesar_y_cifrar_archivo(
            archivo_plano=archivo,
            expediente_obj=self.expediente,
            usuario_creador=self.admin
        )
        self.assertIsNotNone(doc)
        self.assertEqual(doc.nombre_original, 'test.pdf')
        self.assertIsNotNone(doc.hash_sha256)
        self.assertIsNotNone(doc.qr_code_content)
        descifrado = DocumentoSecurizadoService.descifrar_archivo(doc)
        self.assertEqual(descifrado, b'Contenido del documento de prueba')
