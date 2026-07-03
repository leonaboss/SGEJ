from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.utils import timezone
from .models import ModuloBiblioteca
from .forms import ModuloBibliotecaForm

class BibliotecaListView(LoginRequiredMixin, ListView):
    model = ModuloBiblioteca
    template_name = 'biblioteca/biblioteca_list.html'
    context_object_name = 'normativas'
    paginate_by = 20

    def get_queryset(self):
        qs = ModuloBiblioteca.objects.filter(deleted_at__isnull=True)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(titulo__icontains=q)
        tipo = self.request.GET.get('tipo', '').strip()
        if tipo:
            qs = qs.filter(tipo_normativa=tipo)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['tipo_filter'] = self.request.GET.get('tipo', '')
        context['tipos'] = ModuloBiblioteca.TIPOS
        return context

class BibliotecaCreateView(LoginRequiredMixin, View):
    template_name = 'biblioteca/biblioteca_form.html'

    def get(self, request):
        form = ModuloBibliotecaForm()
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

    def post(self, request):
        form = ModuloBibliotecaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Normativa registrada exitosamente.')
            return redirect('biblioteca:lista')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

class BibliotecaUpdateView(LoginRequiredMixin, View):
    template_name = 'biblioteca/biblioteca_form.html'

    def get(self, request, pk):
        obj = ModuloBiblioteca.objects.get(pk=pk, deleted_at__isnull=True)
        form = ModuloBibliotecaForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})

    def post(self, request, pk):
        obj = ModuloBiblioteca.objects.get(pk=pk, deleted_at__isnull=True)
        form = ModuloBibliotecaForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Normativa actualizada exitosamente.')
            return redirect('biblioteca:lista')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})

class BibliotecaDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = ModuloBiblioteca.objects.get(pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Normativa eliminada lógicamente.')
        return redirect('biblioteca:lista')


CAMPOS_BIBLIOTECA = [
    ('titulo', 'Título'),
    ('tipo_normativa', 'Tipo Normativa'),
    ('fecha_publicacion', 'Fecha Publicación'),
]

class ExportarBibliotecaExcelView(LoginRequiredMixin, View):
    def get(self, request):
        from apps.infraestructura.services import ImportExportService
        qs = ModuloBiblioteca.objects.filter(deleted_at__isnull=True)
        return ImportExportService.exportar_modelo_excel(qs, 'Biblioteca', CAMPOS_BIBLIOTECA)


class ImportarBibliotecaExcelView(LoginRequiredMixin, View):
    def post(self, request):
        from apps.infraestructura.services import ImportExportService
        archivo = request.FILES.get('archivo')
        if not archivo:
            messages.error(request, 'Debe seleccionar un archivo Excel.')
            return redirect('biblioteca:lista')
        try:
            creados, errores = ImportExportService.importar_modelo_excel(
                archivo, ModuloBiblioteca, CAMPOS_BIBLIOTECA
            )
            if creados:
                messages.success(request, f'Se importaron {creados} normativas.')
            if errores:
                for e in errores[:3]:
                    messages.warning(request, e)
        except Exception as e:
            messages.error(request, f'Error al importar: {e}')
        return redirect('biblioteca:lista')
