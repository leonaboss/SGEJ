import os
import hashlib
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.db.models import Q
from .models import Documento, PlantillaDocumento
from .forms import DocumentoUploadForm, PlantillaForm
from apps.documentos.services import DocumentoSecurizadoService, PlantillaService
from apps.expedientes.models import Expediente

class DocumentoListView(LoginRequiredMixin, ListView):
    model = Documento
    template_name = 'documentos/documento_list.html'
    context_object_name = 'documentos'
    paginate_by = 20

    def get_queryset(self):
        qs = Documento.objects.filter(deleted_at__isnull=True).select_related(
            'expediente', 'created_by'
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            # Uso de Full-Text Search profesional (vía Manager)
            qs = qs.fulltext_search(q)
        tipo = self.request.GET.get('tipo', '').strip()
        if tipo == 'plantillas':
            qs = qs.filter(es_plantilla=True)
        elif tipo == 'documentos':
            qs = qs.filter(es_plantilla=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['tipo_filter'] = self.request.GET.get('tipo', '')
        return context

class DocumentoUploadView(LoginRequiredMixin, View):
    template_name = 'documentos/documento_upload.html'

    def get(self, request):
        form = DocumentoUploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = DocumentoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            expediente = form.cleaned_data.get('expediente')
            tipo = form.cleaned_data.get('tipo')
            if not expediente:
                messages.error(request, 'Debe seleccionar un expediente.')
                return render(request, self.template_name, {'form': form})
            doc = DocumentoSecurizadoService.procesar_y_cifrar_archivo(
                archivo_plano=archivo,
                expediente_obj=expediente,
                usuario_creador=request.user
            )

            # Crear primera versión
            DocumentVersioningService.crear_version(
                documento=doc,
                archivo_cifrado_path=doc.nombre_cifrado,
                autor=request.user,
                mensaje_commit="Carga inicial"
            )

            if tipo == 'PLANTILLA':
                doc.es_plantilla = True
                doc.save(update_fields=['es_plantilla'])
            messages.success(request, 'Documento subido y cifrado exitosamente.')
            return redirect('documentos:documento_list')
        return render(request, self.template_name, {'form': form})

class DocumentoDetailView(LoginRequiredMixin, DetailView):
    model = Documento
    template_name = 'documentos/documento_detail.html'
    context_object_name = 'documento'

    def get_queryset(self):
        return Documento.objects.filter(deleted_at__isnull=True).select_related(
            'expediente', 'created_by', 'biblioteca'
        )

class DocumentoDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        documento = get_object_or_404(Documento, pk=pk, deleted_at__isnull=True)
        try:
            contenido_descifrado = DocumentoSecurizadoService.descifrar_archivo(documento)
            hash_real = hashlib.sha256(contenido_descifrado).hexdigest()
            if hash_real != documento.hash_sha256:
                response = HttpResponse(
                    '<div style="text-align:center;margin-top:50px;font-family:sans-serif">'
                    '<h1 style="color:red">⚠ Documento Corrupto / Firma Inválida</h1>'
                    f'<p>El hash SHA-256 no coincide. El archivo ha sido alterado.</p>'
                    f'<p>Hash esperado: {documento.hash_sha256}</p>'
                    f'<p>Hash real: {hash_real}</p>'
                    '<a href="/documentos/">Volver</a></div>'
                )
                return response
            filename = documento.nombre_original
            ext = os.path.splitext(filename)[1].lower()
            if ext == '.pdf':
                marca = f"Accedido por: {request.user.get_full_name()} | Cédula: {request.user.cedula} | {timezone.now().strftime('%d/%m/%Y %H:%M')}"
                pdf_con_marca = DocumentoSecurizadoService.aplicar_marca_agua(contenido_descifrado, marca)
                response = HttpResponse(pdf_con_marca, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{documento.nombre_original}"'
                return response
            response = FileResponse(
                contenido_descifrado,
                content_type=documento.tipo_mime,
            )
            response['Content-Disposition'] = f'inline; filename="{documento.nombre_original}"'
            return response
        except FileNotFoundError:
            messages.error(request, 'El archivo físico no se encuentra en el servidor.')
            return redirect('documentos:documento_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error al descifrar el documento: {str(e)}')
            return redirect('documentos:documento_detail', pk=pk)

class DocumentoUpdateView(LoginRequiredMixin, View):
    template_name = 'documentos/documento_upload.html'
    def get(self, request, pk):
        obj = get_object_or_404(Documento, pk=pk, deleted_at__isnull=True)
        from .forms import DocumentoUpdateForm
        form = DocumentoUpdateForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'documento': obj})
    def post(self, request, pk):
        obj = get_object_or_404(Documento, pk=pk, deleted_at__isnull=True)
        from .forms import DocumentoUpdateForm
        form = DocumentoUpdateForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documento actualizado.')
            return redirect('documentos:documento_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'documento': obj})

class DocumentoDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(Documento, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Documento eliminado lógicamente.')
        return redirect('documentos:documento_list')

class PlantillaListView(LoginRequiredMixin, ListView):
    model = PlantillaDocumento
    template_name = 'documentos/plantilla_list.html'
    context_object_name = 'plantillas'
    paginate_by = 20

    def get_queryset(self):
        return PlantillaDocumento.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_salida'] = PlantillaDocumento.TIPOS_SALIDA
        return context


class PlantillaCreateView(LoginRequiredMixin, View):
    template_name = 'documentos/plantilla_form.html'

    def get(self, request):
        form = PlantillaForm()
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

    def post(self, request):
        form = PlantillaForm(request.POST, request.FILES)
        if form.is_valid():
            plantilla = form.save(commit=False)
            plantilla.created_by = request.user
            plantilla.variables = PlantillaService.obtener_variables(plantilla)
            plantilla.save()
            messages.success(request, f'Plantilla "{plantilla.nombre}" creada. {len(plantilla.variables)} variable(s) detectada(s).')
            return redirect('documentos:plantilla_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})


class PlantillaUpdateView(LoginRequiredMixin, View):
    template_name = 'documentos/plantilla_form.html'

    def get(self, request, pk):
        obj = get_object_or_404(PlantillaDocumento, pk=pk, deleted_at__isnull=True)
        form = PlantillaForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'plantilla': obj})

    def post(self, request, pk):
        obj = get_object_or_404(PlantillaDocumento, pk=pk, deleted_at__isnull=True)
        form = PlantillaForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            plantilla = form.save(commit=False)
            if 'archivo_plantilla' in request.FILES:
                plantilla.variables = PlantillaService.obtener_variables(plantilla)
            plantilla.save()
            messages.success(request, f'Plantilla "{plantilla.nombre}" actualizada.')
            return redirect('documentos:plantilla_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'plantilla': obj})


class PlantillaDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(PlantillaDocumento, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Plantilla eliminada lógicamente.')
        return redirect('documentos:plantilla_list')


class PlantillaGenerarView(LoginRequiredMixin, View):
    template_name = 'documentos/plantilla_generar.html'

    def get(self, request, pk):
        plantilla = get_object_or_404(PlantillaDocumento, pk=pk, deleted_at__isnull=True)
        from django import forms as django_forms

        class VariablesForm(django_forms.Form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for var in plantilla.variables:
                    nombre = var if isinstance(var, str) else var.get('nombre', '')
                    etiqueta = var if isinstance(var, str) else var.get('etiqueta', nombre)
                    tipo = 'text' if isinstance(var, str) else var.get('tipo', 'text')
                    field_kwargs = {
                        'label': etiqueta,
                        'required': True,
                        'widget': django_forms.TextInput(attrs={'class': 'form-control', 'placeholder': etiqueta}),
                    }
                    if tipo == 'date':
                        field_kwargs['widget'] = django_forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
                    elif tipo == 'textarea':
                        field_kwargs['widget'] = django_forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                    self.fields[nombre] = django_forms.CharField(**field_kwargs)

            expediente = django_forms.ModelChoiceField(
                queryset=Expediente.objects.filter(deleted_at__isnull=True),
                required=False, label='Expediente (opcional)',
                widget=django_forms.Select(attrs={'class': 'form-select'}),
            )

        form = VariablesForm()
        return render(request, self.template_name, {
            'plantilla': plantilla,
            'form': form,
        })

    def post(self, request, pk):
        plantilla = get_object_or_404(PlantillaDocumento, pk=pk, deleted_at__isnull=True)
        from django import forms as django_forms

        class VariablesForm(django_forms.Form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for var in plantilla.variables:
                    nombre = var if isinstance(var, str) else var.get('nombre', '')
                    etiqueta = var if isinstance(var, str) else var.get('etiqueta', nombre)
                    self.fields[nombre] = django_forms.CharField(
                        label=etiqueta, required=True,
                        widget=django_forms.TextInput(attrs={'class': 'form-control'})
                    )

            expediente = django_forms.ModelChoiceField(
                queryset=Expediente.objects.filter(deleted_at__isnull=True),
                required=False, label='Expediente (opcional)',
                widget=django_forms.Select(attrs={'class': 'form-select'}),
            )

        form = VariablesForm(request.POST)
        if form.is_valid():
            valores = {k: v for k, v in form.cleaned_data.items() if k != 'expediente'}
            expediente = form.cleaned_data.get('expediente')
            doc = PlantillaService.generar_documento(
                plantilla=plantilla,
                valores=valores,
                usuario=request.user,
                expediente=expediente,
            )
            messages.success(request, f'Documento "{doc.nombre_original}" generado exitosamente.')
            return redirect('documentos:documento_detail', pk=doc.pk)
        return render(request, self.template_name, {
            'plantilla': plantilla,
            'form': form,
        })


class PlantillaPreviewVariablesView(LoginRequiredMixin, View):
    def get(self, request, pk):
        plantilla = get_object_or_404(PlantillaDocumento, pk=pk, deleted_at__isnull=True)
        from django.http import JsonResponse
        return JsonResponse({'variables': plantilla.variables})


CAMPOS_DOCUMENTOS = [
    ('nombre_original', 'Nombre Original'),
    ('tipo_mime', 'Tipo MIME'),
    ('expediente__numero_expediente', 'Expediente'),
    ('version', 'Versión'),
    ('created_by__get_full_name', 'Usuario'),
    ('created_at', 'Fecha'),
]

class ImportarDocumentosExcelView(LoginRequiredMixin, View):
    def post(self, request):
        from apps.infraestructura.services import ImportExportService
        from .models import Documento
        archivo = request.FILES.get('archivo')
        if not archivo:
            messages.error(request, 'Debe seleccionar un archivo Excel.')
            return redirect('documentos:documento_list')
        try:
            creados, errores = ImportExportService.importar_modelo_excel(
                archivo, Documento, CAMPOS_DOCUMENTOS,
                extra_defaults={'version': 1, 'created_by': request.user, 'nombre_cifrado': '', 'hash_sha256': '', 'iv_cifrado': ''}
            )
            if creados:
                messages.success(request, f'Se importaron {creados} documentos.')
            if errores:
                for e in errores[:3]:
                    messages.warning(request, e)
        except Exception as e:
            messages.error(request, f'Error al importar: {e}')
        return redirect('documentos:documento_list')

class ExportarDocumentosExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Documento.objects.filter(deleted_at__isnull=True).select_related('expediente', 'created_by')
        from apps.infraestructura.services import ImportExportService
        return ImportExportService.exportar_modelo_excel(qs, 'Documentos', CAMPOS_DOCUMENTOS)
