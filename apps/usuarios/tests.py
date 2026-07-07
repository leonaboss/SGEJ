from django import forms
from django.core import mail
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from faker import Faker
from .forms import validate_password_strength
from .models import Usuario, HistorialContrasena
from apps.expedientes.models import Personal

fake = Faker('es_VE')

class UsuarioModelTest(TestCase):
    def setUp(self):
        self.personal_admin = Personal.objects.create(
            nombres=fake.first_name(), apellidos=fake.last_name(), cedula=fake.unique.numerify(text='##########')
        )
        self.admin = Usuario.objects.create_superuser(
            usuario=fake.user_name(), password=fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
            personal=self.personal_admin, cedula=self.personal_admin.cedula
        )
        self.personal_abogado = Personal.objects.create(
            nombres=fake.first_name(), apellidos=fake.last_name(), cedula=fake.unique.numerify(text='##########')
        )
        self.abogado = Usuario.objects.create_user(
            usuario=fake.user_name(), password=fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
            personal=self.personal_abogado, cedula=self.personal_abogado.cedula,
            rol='ABOG'
        )
        self.personal_publico = Personal.objects.create(
            nombres=fake.first_name(), apellidos=fake.last_name(), cedula=fake.unique.numerify(text='##########')
        )
        self.publico = Usuario.objects.create_user(
            usuario=fake.user_name(), password=fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
            personal=self.personal_publico, cedula=self.personal_publico.cedula,
            rol='USR_PUBLICO'
        )

    def test_roles(self):
        self.assertEqual(self.admin.rol, 'ADMIN')
        self.assertEqual(self.abogado.rol, 'ABOG')
        self.assertEqual(self.publico.rol, 'USR_PUBLICO')

    def test_get_full_name(self):
        full_name = f"{self.personal_admin.nombres} {self.personal_admin.apellidos}"
        self.assertEqual(self.admin.get_full_name(), full_name)

    def test_get_rol_display_label(self):
        self.assertEqual(self.admin.get_rol_display_label(), 'Administrador')
        self.assertEqual(self.abogado.get_rol_display_label(), 'Abogado')

    def test_default_rol(self):
        cedula_default = fake.unique.numerify(text='##########')
        personal_default = Personal.objects.create(
            nombres=fake.first_name(), apellidos=fake.last_name(), cedula=cedula_default
        )
        user = Usuario.objects.create_user(
            usuario=fake.user_name(), password=fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
            personal=personal_default, cedula=cedula_default
        )
        self.assertEqual(user.rol, 'USR_PUBLICO')

    def test_password_history_on_change(self):
        self.admin.set_password('NuevaClave!!1Segura')
        self.admin._password_plana_temporal = 'NuevaClave!!1Segura'
        self.admin.save()
        historial = HistorialContrasena.objects.filter(usuario=self.admin)
        self.assertEqual(historial.count(), 1)


class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        self.username = fake.user_name()
        self.personal = Personal.objects.create(
            nombres=fake.first_name(), apellidos=fake.last_name(), cedula=fake.unique.numerify(text='##########')
        )
        self.user = Usuario.objects.create_superuser(
            usuario=self.username, password=self.password,
            personal=self.personal, cedula=self.personal.cedula
        )

    def test_login_success(self):
        response = self.client.post(reverse('usuarios:login'), {
            'usuario': self.username, 'password': self.password
        })
        self.assertRedirects(response, reverse('expedientes:dashboard'))

    def test_login_invalid_password(self):
        response = self.client.post(reverse('usuarios:login'), {
            'usuario': self.username, 'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.intentos_fallidos, 1)

    def test_login_bloqueado_tras_3_intentos(self):
        for _ in range(3):
            self.client.post(reverse('usuarios:login'), {
                'usuario': self.username, 'password': 'wrongpass'
            })
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_bloqueado)

    def test_login_bloqueado_rejected(self):
        self.user.is_bloqueado = True
        self.user.save()
        response = self.client.post(reverse('usuarios:login'), {
            'usuario': self.username, 'password': self.password
        })
        self.assertContains(response, 'bloqueada')


class RBACTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.personal_admin = Personal.objects.create(
            nombres='Admin', apellidos='Test', cedula='30000001'
        )
        self.admin = Usuario.objects.create_superuser(
            usuario='admin', password='Clave1234!!Segura',
            personal=self.personal_admin, cedula='30000001'
        )
        self.personal_abogado = Personal.objects.create(
            nombres='Abogado', apellidos='Test', cedula='30000002'
        )
        self.abogado = Usuario.objects.create_user(
            usuario='abogado', password='Clave1234!!Segura',
            personal=self.personal_abogado, cedula='30000002',
            rol='ABOG'
        )
        self.personal_publico = Personal.objects.create(
            nombres='Publico', apellidos='Test', cedula='30000003'
        )
        self.publico = Usuario.objects.create_user(
            usuario='publico', password='Clave1234!!Segura',
            personal=self.personal_publico, cedula='30000003',
            rol='USR_PUBLICO'
        )

    def test_admin_ver_lista_usuarios(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.get(reverse('usuarios:usuario_list'))
        self.assertEqual(response.status_code, 200)

    def test_abogado_ver_lista_usuarios(self):
        self.client.login(usuario='abogado', password='Clave1234!!Segura')
        response = self.client.get(reverse('usuarios:usuario_list'))
        self.assertEqual(response.status_code, 200)

    def test_publico_no_ver_lista_usuarios(self):
        self.client.login(usuario='publico', password='Clave1234!!Segura')
        response = self.client.get(reverse('usuarios:usuario_list'))
        self.assertRedirects(response, reverse('expedientes:dashboard'))

    def test_abogado_no_crear_admin(self):
        self.client.login(usuario='abogado', password='Clave1234!!Segura')
        personal_nuevo = Personal.objects.create(nombres='Nuevo', apellidos='Admin', cedula='40000001')
        response = self.client.post(reverse('usuarios:usuario_create'), {
            'usuario': 'nuevo_admin',
            'personal': personal_nuevo.id,
            'cedula': '40000001',
            'rol': 'ADMIN',
            'password': 'Clave1234!!Segura',
            'password_repeat': 'Clave1234!!Segura',
        })
        self.assertFalse(Usuario.objects.filter(usuario='nuevo_admin').exists())

    def test_abogado_crear_abogado(self):
        self.client.login(usuario='abogado', password='Clave1234!!Segura')
        personal_nuevo = Personal.objects.create(nombres='Nuevo', apellidos='Abogado', cedula='40000002')
        response = self.client.post(reverse('usuarios:usuario_create'), {
            'usuario': 'nuevo_abog',
            'personal': personal_nuevo.id,
            'cedula': '40000002',
            'rol': 'ABOG',
            'password': 'Clave1234!!Segura',
            'password_repeat': 'Clave1234!!Segura',
        })
        self.assertTrue(Usuario.objects.filter(usuario='nuevo_abog').exists())

    def test_admin_crear_admin(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        personal_nuevo = Personal.objects.create(nombres='Nuevo', apellidos='Admin2', cedula='40000003')
        response = self.client.post(reverse('usuarios:usuario_create'), {
            'usuario': 'nuevo_admin2',
            'personal': personal_nuevo.id,
            'cedula': '40000003',
            'rol': 'ADMIN',
            'password': 'Clave1234!!Segura',
            'password_repeat': 'Clave1234!!Segura',
        })
        self.assertTrue(Usuario.objects.filter(usuario='nuevo_admin2').exists())


class FormTest(TestCase):
    def setUp(self):
        self.personal_admin = Personal.objects.create(
            nombres='Admin', apellidos='Test', cedula='50000001'
        )
        self.admin = Usuario.objects.create_superuser(
            usuario='admin', password='Clave1234!!Segura',
            personal=self.personal_admin, cedula='50000001'
        )

    def test_validate_password_strength_requires_uppercase(self):
        with self.assertRaises(forms.ValidationError):
            validate_password_strength('clave1234!!segura')

    @override_settings(ENTORNO='produccion', EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_recuperacion_envia_codigo_por_correo_en_produccion(self):
        self.personal_admin = Personal.objects.create(
            nombres='Admin', apellidos='Test', cedula='50000002'
        )
        user = Usuario.objects.create_user(
            usuario='recuperar_correo',
            password='Clave1234!!Segura',
            personal=self.personal_admin,
            cedula='50000002',
            correo='usuario@test.com',
            rol='USR_PUBLICO'
        )
        response = self.client.post(reverse('usuarios:recovery'), {'usuario': user.usuario, 'stage': 'email'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Código de Verificación')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Recuperación de Contraseña', mail.outbox[0].subject)
        self.assertIn('código', mail.outbox[0].body.lower())

    @override_settings(
        ENTORNO='localhost',
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='no-reply@test.com',
        EMAIL_HOST='smtp.test.com',
        EMAIL_HOST_USER='user@test.com',
        EMAIL_HOST_PASSWORD='secret',
    )
    def test_recuperacion_usa_email_si_hay_configuracion_smtp(self):
        self.personal_admin = Personal.objects.create(
            nombres='Admin', apellidos='Test', cedula='50000003'
        )
        user = Usuario.objects.create_user(
            usuario='recuperar_auto',
            password='Clave1234!!Segura',
            personal=self.personal_admin,
            cedula='50000003',
            correo='auto@test.com',
            rol='USR_PUBLICO'
        )
        response = self.client.post(reverse('usuarios:recovery'), {'usuario': user.usuario, 'stage': 'email'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Código de Verificación')
        self.assertEqual(len(mail.outbox), 1)

    def test_creacion_form_valido(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        personal_nuevo = Personal.objects.create(nombres='Nuevo', apellidos='Usuario', cedula='50000002')
        response = self.client.post(reverse('usuarios:usuario_create'), {
            'usuario': 'nuevo',
            'personal': personal_nuevo.id,
            'cedula': '50000002',
            'rol': 'ABOG',
            'password': 'Clave1234!!Segura',
            'password_repeat': 'Clave1234!!Segura',
        })
        self.assertEqual(response.status_code, 302)

    def test_creacion_form_passwords_no_coinciden(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        personal_nuevo = Personal.objects.create(nombres='Nuevo', apellidos='Usuario', cedula='50000003')
        response = self.client.post(reverse('usuarios:usuario_create'), {
            'usuario': 'nuevo2',
            'personal': personal_nuevo.id,
            'cedula': '50000003',
            'rol': 'ABOG',
            'password': 'Clave1234!!Segura',
            'password_repeat': 'otraclave',
        })
        self.assertEqual(response.status_code, 200)

    def test_creacion_form_cedula_invalida(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        personal_nuevo = Personal.objects.create(nombres='Nuevo', apellidos='Usuario', cedula='ABC123')
        response = self.client.post(reverse('usuarios:usuario_create'), {
            'usuario': 'nuevo3',
            'personal': personal_nuevo.id,
            'cedula': 'ABC123',
            'rol': 'ABOG',
            'password': 'Clave1234!!Segura',
            'password_repeat': 'Clave1234!!Segura',
        })
        self.assertEqual(response.status_code, 200)
