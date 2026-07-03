from django.test import TestCase, Client
from django.urls import reverse
from apps.usuarios.models import Usuario
from .models import Personal, Motivo, Tribunal, Expediente


class ExpedienteModelTest(TestCase):
    def setUp(self):
        personal_admin = Personal.objects.create(
            nombres='Admin', apellidos='Test', cedula='10000001'
        )
        self.admin = Usuario.objects.create_superuser(
            usuario='admin', password='Clave1234!!Segura',
            personal=personal_admin, cedula='10000001'
        )
        self.personal = Personal.objects.create(
            nombres='Juan', apellidos='Perez', cedula='20000001'
        )
        self.motivo = Motivo.objects.create(
            descripcion='Despido injustificado', tipo='LAB'
        )
        self.tribunal = Tribunal.objects.create(
            nombre='Tribunal Supremo', tipo='CONT'
        )

    def test_crear_expediente(self):
        exp = Expediente.objects.create(
            numero_expediente='EXP-2026-001',
            tipo_modulo='DESP',
            usuario=self.admin,
            personal=self.personal,
            motivo=self.motivo,
            estatus='RECIBIDO'
        )
        self.assertIn('EXP-2026-001', str(exp))
        self.assertFalse(exp.is_archivado)

    def test_soft_delete(self):
        exp = Expediente.objects.create(
            numero_expediente='EXP-2026-002',
            tipo_modulo='INSP',
            usuario=self.admin,
            personal=self.personal
        )
        from django.utils import timezone
        exp.deleted_at = timezone.now()
        exp.save()
        self.assertIsNotNone(exp.deleted_at)


class DashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        personal_admin = Personal.objects.create(
            nombres='Admin', apellidos='Test', cedula='30000001'
        )
        self.admin = Usuario.objects.create_superuser(
            usuario='admin', password='Clave1234!!Segura',
            personal=personal_admin, cedula='30000001'
        )
        personal_desp = Personal.objects.create(
            nombres='Desp', apellidos='Test', cedula='30000002'
        )
        for i in range(3):
            Expediente.objects.create(
                numero_expediente=f'DESP-2026-{i:03d}',
                tipo_modulo='DESP',
                personal=personal_desp,
                usuario=self.admin
            )
        personal_insp = Personal.objects.create(
            nombres='Insp', apellidos='Test', cedula='30000003'
        )
        for i in range(2):
            Expediente.objects.create(
                numero_expediente=f'INSP-2026-{i:03d}',
                tipo_modulo='INSP',
                personal=personal_insp,
                usuario=self.admin
            )

    def test_dashboard_accessible(self):
        login_ok = self.client.login(usuario='admin', password='Clave1234!!Segura')
        self.assertTrue(login_ok, msg='El login debería funcionar')
        response = self.client.get(reverse('expedientes:dashboard'))
        if response.status_code == 302:
            self.fail(f'Dashboard redirige a: {response.url}')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_counts_api(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.get(reverse('expedientes:api_dashboard_counts'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['despido'], 3)
        self.assertEqual(data['inspectoria'], 2)


class APITest(TestCase):
    def setUp(self):
        self.client = Client()
        personal_admin = Personal.objects.create(
            nombres='Admin', apellidos='Test', cedula='40000001'
        )
        self.admin = Usuario.objects.create_superuser(
            usuario='admin', password='Clave1234!!Segura',
            personal=personal_admin, cedula='40000001'
        )
        self.client.login(usuario='admin', password='Clave1234!!Segura')

    def test_api_expedientes_list(self):
        response = self.client.get(reverse('expedientes-list'))
        self.assertEqual(response.status_code, 200)
