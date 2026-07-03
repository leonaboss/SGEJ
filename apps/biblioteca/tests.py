# pyrefly: ignore [missing-import]
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import ModuloBiblioteca


class ModuloBibliotecaModelTest(TestCase):
    def setUp(self):
        self.normativa = ModuloBiblioteca.objects.create(
            titulo='Reglamento Interno UPTAG',
            tipo_normativa='REGL',
            fecha_publicacion=timezone.now().date(),
        )

    def test_creacion_normativa(self):
        self.assertEqual(self.normativa.titulo, 'Reglamento Interno UPTAG')
        self.assertEqual(self.normativa.tipo_normativa, 'REGL')

    def test_str_method(self):
        self.assertEqual(str(self.normativa), 'Reglamento Interno UPTAG')

    def test_get_tipo_normativa_display(self):
        self.assertEqual(self.normativa.get_tipo_normativa_display(), 'Reglamento Interno')

    def test_soft_delete(self):
        self.normativa.deleted_at = timezone.now()
        self.normativa.save(update_fields=['deleted_at'])
        qs = ModuloBiblioteca.objects.filter(deleted_at__isnull=True)
        self.assertNotIn(self.normativa, qs)

    def test_ordering(self):
        n2 = ModuloBiblioteca.objects.create(
            titulo='Gaceta Oficial 2024',
            tipo_normativa='GAC',
            fecha_publicacion=timezone.now().date(),
        )
        qs = ModuloBiblioteca.objects.all()
        self.assertEqual(qs.first(), n2)


class BibliotecaViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        from apps.usuarios.models import Usuario
        from apps.expedientes.models import Personal
        personal = Personal.objects.create(
            nombres='Admin', apellidos='Test', cedula='70000001'
        )
        self.admin = Usuario.objects.create_superuser(
            usuario='admin', password='Clave1234!!Segura',
            personal=personal, cedula='70000001'
        )
        self.normativa = ModuloBiblioteca.objects.create(
            titulo='Reglamento Interno',
            tipo_normativa='REGL',
            fecha_publicacion=timezone.now().date(),
        )

    def test_lista_requiere_login(self):
        response = self.client.get(reverse('biblioteca:lista'))
        self.assertRedirects(response, f'/auth/login/?next={reverse("biblioteca:lista")}')

    def test_lista_accessible(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.get(reverse('biblioteca:lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reglamento Interno')

    def test_lista_filtro_titulo(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.get(reverse('biblioteca:lista'), {'q': 'Reglamento'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reglamento Interno')

    def test_lista_filtro_tipo(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.get(reverse('biblioteca:lista'), {'tipo': 'REGL'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reglamento Interno')

    def test_lista_filtro_tipo_sin_resultados(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.get(reverse('biblioteca:lista'), {'tipo': 'GAC'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No hay normativas registradas')

    def test_crear_view_get(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.get(reverse('biblioteca:crear'))
        self.assertEqual(response.status_code, 200)

    def test_crear_view_post(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.post(reverse('biblioteca:crear'), {
            'titulo': 'Nueva Normativa',
            'tipo_normativa': 'GAC',
            'fecha_publicacion': '2024-01-15',
        })
        self.assertRedirects(response, reverse('biblioteca:lista'))
        self.assertTrue(ModuloBiblioteca.objects.filter(titulo='Nueva Normativa').exists())

    def test_crear_view_post_invalido(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.post(reverse('biblioteca:crear'), {
            'titulo': '',
            'tipo_normativa': 'GAC',
        })
        self.assertEqual(response.status_code, 200)

    def test_editar_view_get(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.get(reverse('biblioteca:editar', args=[self.normativa.pk]))
        self.assertEqual(response.status_code, 200)

    def test_editar_view_post(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.post(reverse('biblioteca:editar', args=[self.normativa.pk]), {
            'titulo': 'Título Actualizado',
            'tipo_normativa': 'REGL',
            'fecha_publicacion': '2024-06-01',
        })
        self.assertRedirects(response, reverse('biblioteca:lista'))
        self.normativa.refresh_from_db()
        self.assertEqual(self.normativa.titulo, 'Título Actualizado')

    def test_eliminar_view(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.post(reverse('biblioteca:eliminar', args=[self.normativa.pk]))
        self.assertRedirects(response, reverse('biblioteca:lista'))
        self.normativa.refresh_from_db()
        self.assertIsNotNone(self.normativa.deleted_at)

    def test_exportar_excel(self):
        self.client.login(usuario='admin', password='Clave1234!!Segura')
        response = self.client.get(reverse('biblioteca:exportar'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
