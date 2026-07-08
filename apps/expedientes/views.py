from django.contrib.contenttypes.models import ContentType
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse_lazy
import datetime
from datetime import timedelta

from .models import (
    Expediente, Notificacion, AudienciaAgenda, Personal, Cargo, PersonaCargo,
    Motivo, Tribunal, Actuacion, LitigioContraparte, SustanciacionNotificacion,
    SujetoProcesal
)
from .forms import (
    ExpedienteForm, PersonalForm, CargoForm, MotivoForm, TribunalForm,
    ActuacionForm, AudienciaAgendaForm, PersonaCargoForm,
    LitigioContraparteForm, SustanciacionNotificacionForm,
    SujetoProcesalForm
)
from .services import AlertasService
from apps.infraestructura.services import ImportExportService


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activos = Expediente.objects.filter(is_archivado=False, deleted_at__isnull=True)
        context['counts'] = {
            'despido': activos.filter(tipo_modulo='DESP').count(),
            'inspectoria': activos.filter(tipo_modulo='INSP').count(),
            'oficina': activos.filter(tipo_modulo='OFIC').count(),
            'convenios': activos.filter(tipo_modulo='CONT').count(),
            'litigios': activos.filter(tipo_modulo='LITI').count(),
            'sustanciacion': activos.filter(tipo_modulo='SUST').count(),
            'indices': activos.filter(tipo_modulo='IND').count(),
            'actuaciones': Actuacion.objects.filter(deleted_at__isnull=True).count(),
        }
        context['historial_reciente'] = Expediente.objects.filter(
            deleted_at__isnull=True
        ).select_related('personal', 'usuario').order_by('-created_at')[:10]

        hoy = timezone.now().date()
        context['alertas_vencimiento'] = Expediente.objects.filter(
            tipo_modulo='CONT', fecha_vencimiento__isnull=False,
            fecha_vencimiento__lte=hoy + timedelta(days=90),
            fecha_vencimiento__gte=hoy, is_archivado=False,
            deleted_at__isnull=True,
        ).order_by('fecha_vencimiento')

        context['notificaciones_count'] = Notificacion.objects.filter(
            usuario=self.request.user, leido=False, deleted_at__isnull=True
        ).count()
        return context


class DashboardCountsAPIView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        activos = Expediente.objects.for_user(request.user).filter(is_archivado=False, deleted_at__isnull=True)
        counts = {
            'despido': activos.filter(tipo_modulo='DESP').count(),
            'inspectoria': activos.filter(tipo_modulo='INSP').count(),
            'oficina': activos.filter(tipo_modulo='OFIC').count(),
            'convenios': activos.filter(tipo_modulo='CONT').count(),
            'litigios': activos.filter(tipo_modulo='LITI').count(),
            'sustanciacion': activos.filter(tipo_modulo='SUST').count(),
            'indices': activos.filter(tipo_modulo='IND').count(),
            'actuaciones': Actuacion.objects.for_user(request.user).filter(deleted_at__isnull=True).count(),
        }
        return JsonResponse(counts)


class ExpedienteModuloListView(LoginRequiredMixin, ListView):
    model = Expediente
    context_object_name = 'expedientes'
    paginate_by = 20

    TEMPLATE_MAP = {
        'DESP': 'expedientes/despido_list.html',
        'INSP': 'expedientes/inspectoria_list.html',
        'OFIC': 'expedientes/oficina_list.html',
        'CONT': 'expedientes/convenios_list.html',
        'LITI': 'expedientes/litigios_list.html',
        'SUST': 'expedientes/sustanciacion_list.html',
        'IND': 'expedientes/indices_list.html',
    }
    MODULE_NAMES = {
        'DESP': 'Calificación de Despido',
        'INSP': 'Casos de Inspectoría',
        'OFIC': 'Oficina Jurídica',
        'CONT': 'Convenios UPTAG',
        'LITI': 'Litigios',
        'SUST': 'Sustanciación Disciplinaria',
        'IND': 'Índices de Inspectoría',
    }

    def get_template_names(self):
        tipo = self.kwargs.get('tipo_modulo', 'DESP')
        return [self.TEMPLATE_MAP.get(tipo, 'expedientes/despido_list.html')]

    def get_queryset(self):
        tipo = self.kwargs.get('tipo_modulo', 'DESP')
        queryset = Expediente.objects.for_user(self.request.user).filter(
            tipo_modulo=tipo, deleted_at__isnull=True
        ).select_related('personal', 'motivo', 'cargo', 'tribunal', 'usuario')
        if tipo == 'SUST':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'sustanciacionnotificacion_set',
                    queryset=SustanciacionNotificacion.objects.filter(deleted_at__isnull=True).order_by('-created_at'),
                    to_attr='notificaciones_sust'
                )
            )
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(numero_expediente__icontains=q) |
                Q(personal__nombres__icontains=q) |
                Q(personal__apellidos__icontains=q) |
                Q(personal__cedula__icontains=q)
            )
        estatus = self.request.GET.get('estatus', '').strip()
        if estatus:
            queryset = queryset.filter(estatus=estatus)
        fase = self.request.GET.get('fase', '').strip()
        if fase:
            queryset = queryset.filter(fase_actual=fase)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = self.kwargs.get('tipo_modulo', 'DESP')
        context['tipo_modulo'] = tipo
        context['module_name'] = self.MODULE_NAMES.get(tipo, 'Expedientes')
        context['search_query'] = self.request.GET.get('q', '')
        context['estatus_filter'] = self.request.GET.get('estatus', '')
        context['fase_actual'] = self.request.GET.get('fase', '')
        context['estatus_choices'] = Expediente.EstatusChoices.choices
        context['mostrar_filtro_estatus'] = tipo in ('DESP', 'LITI', 'OFIC')
        context['notificaciones_count'] = Notificacion.objects.filter(
            usuario=self.request.user, leido=False, deleted_at__isnull=True
        ).count()
        return context


class ExpedienteDetailView(LoginRequiredMixin, DetailView):
    model = Expediente
    template_name = 'expedientes/expediente_detail.html'
    context_object_name = 'expediente'

    def get_queryset(self):
        return Expediente.objects.filter(
            deleted_at__isnull=True
        ).select_related('personal', 'motivo', 'cargo', 'tribunal', 'usuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notificaciones_count'] = Notificacion.objects.filter(
            usuario=self.request.user, leido=False, deleted_at__isnull=True
        ).count()
        
        # Filtramos actuaciones por el objeto actual (usando GenericRelation si existiera, o filtrando por content_type)
        context['actuaciones'] = Actuacion.objects.filter(
            content_type=ContentType.objects.get_for_model(Expediente),
            object_id=self.object.pk,
            deleted_at__isnull=True
        ).select_related('usuario').order_by('-created_at')
        
        context['audiencias'] = AudienciaAgenda.objects.filter(
            expediente=self.object, deleted_at__isnull=True
        ).order_by('fecha_hora')
        context['contrapartes'] = LitigioContraparte.objects.filter(
            expediente=self.object, deleted_at__isnull=True
        )
        return context


class ExpedienteCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/expediente_form.html'

    def get(self, request):
        initial = {}
        tipo_modulo = request.GET.get('tipo_modulo')
        if tipo_modulo:
            initial['tipo_modulo'] = tipo_modulo
        form = ExpedienteForm(initial=initial)
        return render(request, self.template_name, {
            'form': form, 'accion': 'Crear', 'tipo_modulo': tipo_modulo,
        })

    def post(self, request):
        form = ExpedienteForm(request.POST)
        tipo_modulo = request.POST.get('tipo_modulo') or request.GET.get('tipo_modulo')
        if form.is_valid():
            expediente = form.save(commit=False)
            expediente.usuario = request.user
            expediente.save()
            self._crear_eventos_litigios(expediente)
            messages.success(request, f'Expediente {expediente.numero_expediente} creado.')
            if expediente.tipo_modulo:
                return redirect('expedientes:modulo_list', tipo_modulo=expediente.tipo_modulo)
            return redirect('expedientes:expediente_detail', pk=expediente.pk)
        return render(request, self.template_name, {
            'form': form, 'accion': 'Crear', 'tipo_modulo': tipo_modulo,
        })

    def _crear_eventos_litigios(self, expediente):
        if expediente.tipo_modulo != 'LITI':
            return
        if not expediente.fecha_demanda:
            return
        base = expediente.fecha_demanda
        eventos = [
            ('Audiencia de Mediación', 'AUD',
             base + datetime.timedelta(days=30),
             'Juzgado correspondiente',
             'Audiencia de mediación según LOTTT.'),
            ('Lapso de Contestación', 'LAPS',
             base + datetime.timedelta(days=20),
             '', 'Vence el lapso para contestar la demanda.'),
            ('Lapso de Promoción de Pruebas', 'LAPS',
             base + datetime.timedelta(days=50),
             '', 'Vence el lapso de promoción de pruebas.'),
            ('Audiencia de Juicio', 'AUD',
             base + datetime.timedelta(days=90),
             'Tribunal de la causa',
             'Audiencia oral de juicio.'),
            ('Sentencia Estimada', 'VENC',
             base + datetime.timedelta(days=150),
             '', 'Fecha estimada de sentencia.'),
        ]
        for titulo, tipo, fecha, lugar, desc in eventos:
            AudienciaAgenda.objects.create(
                expediente=expediente,
                titulo=titulo,
                tipo_evento=tipo,
                fecha_hora=timezone.make_aware(
                    datetime.datetime.combine(fecha, datetime.time(8, 0))
                ),
                lugar=lugar,
                descripcion=desc,
                alerta_email=True,
                usuario=expediente.usuario,
            )


class ExpedienteUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/expediente_form.html'

    def get(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk, deleted_at__isnull=True)
        form = ExpedienteForm(instance=expediente)
        return render(request, self.template_name, {
            'form': form, 'accion': 'Editar', 'expediente': expediente,
            'tipo_modulo': expediente.tipo_modulo,
        })

    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk, deleted_at__isnull=True)
        form = ExpedienteForm(request.POST, instance=expediente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expediente actualizado.')
            return redirect('expedientes:expediente_detail', pk=expediente.pk)
        return render(request, self.template_name, {
            'form': form, 'accion': 'Editar', 'expediente': expediente,
            'tipo_modulo': expediente.tipo_modulo,
        })


class ExpedienteDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk, deleted_at__isnull=True)
        expediente.deleted_at = timezone.now()
        expediente.save(update_fields=['deleted_at'])
        messages.success(request, 'Expediente eliminado lógicamente.')
        return redirect('expedientes:dashboard')


class ExpedienteArchivadosListView(LoginRequiredMixin, ListView):
    model = Expediente
    template_name = 'expedientes/archivados_list.html'
    context_object_name = 'expedientes'
    paginate_by = 20

    def get_queryset(self):
        qs = Expediente.objects.for_user(self.request.user).filter(
            is_archivado=True, deleted_at__isnull=True
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                models.Q(numero_expediente__icontains=q) |
                models.Q(personal__nombres__icontains=q) |
                models.Q(personal__apellidos__icontains=q) |
                models.Q(personal__cedula__icontains=q)
            )
        return qs.select_related('personal', 'motivo', 'cargo', 'tribunal', 'usuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ActuacionListView(LoginRequiredMixin, ListView):
    model = Actuacion
    template_name = 'expedientes/actuacion_list.html'
    context_object_name = 'actuaciones'
    paginate_by = 25

    def get_queryset(self):
        # Mantenemos el filtro por usuario si el modelo Actuacion lo soporta
        qs = Actuacion.objects.for_user(self.request.user).filter(deleted_at__isnull=True).select_related('usuario', 'content_type')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(descripcion__icontains=q)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['es_admin'] = self.request.user.rol == 'ADMIN'
        return context


class ActuacionCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/actuacion_form.html'

    def get(self, request, expediente_pk):
        expediente = get_object_or_404(Expediente, pk=expediente_pk, deleted_at__isnull=True)
        form = ActuacionForm(initial={'expediente': expediente})
        return render(request, self.template_name, {'form': form, 'expediente': expediente})

    def post(self, request, expediente_pk):
        expediente = get_object_or_404(Expediente, pk=expediente_pk, deleted_at__isnull=True)
        form = ActuacionForm(request.POST)
        if form.is_valid():
            actuacion = form.save(commit=False)
            actuacion.content_object = expediente
            actuacion.usuario = request.user
            actuacion.save()
            messages.success(request, 'Actuación registrada.')
            return redirect('expedientes:expediente_detail', pk=expediente.pk)
        return render(request, self.template_name, {'form': form, 'expediente': expediente})


class ActuacionUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/actuacion_form.html'

    def get(self, request, pk):
        actuacion = get_object_or_404(Actuacion, pk=pk, deleted_at__isnull=True)
        form = ActuacionForm(instance=actuacion)
        return render(request, self.template_name, {
            'form': form, 'accion': 'Editar', 'actuacion': actuacion,
            'expediente': actuacion.expediente,
        })

    def post(self, request, pk):
        actuacion = get_object_or_404(Actuacion, pk=pk, deleted_at__isnull=True)
        form = ActuacionForm(request.POST, instance=actuacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Actuación actualizada.')
            return redirect('expedientes:expediente_detail', pk=actuacion.expediente.pk)
        return render(request, self.template_name, {
            'form': form, 'accion': 'Editar', 'actuacion': actuacion,
            'expediente': actuacion.expediente,
        })


class ActuacionDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        actuacion = get_object_or_404(Actuacion, pk=pk, deleted_at__isnull=True)
        expediente_pk = None
        if actuacion.content_type.model == 'expediente':
            expediente_pk = actuacion.object_id
        actuacion.deleted_at = timezone.now()
        actuacion.save(update_fields=['deleted_at'])
        messages.success(request, 'Actuación eliminada.')
        if expediente_pk:
            return redirect('expedientes:expediente_detail', pk=expediente_pk)
        return redirect('expedientes:dashboard')


class AudienciaAgendaCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/audiencia_form.html'

    def get(self, request, expediente_pk):
        expediente = get_object_or_404(Expediente, pk=expediente_pk, deleted_at__isnull=True)
        form = AudienciaAgendaForm(initial={'expediente': expediente})
        return render(request, self.template_name, {'form': form, 'expediente': expediente})

    def post(self, request, expediente_pk):
        expediente = get_object_or_404(Expediente, pk=expediente_pk, deleted_at__isnull=True)
        form = AudienciaAgendaForm(request.POST)
        if form.is_valid():
            audiencia = form.save(commit=False)
            audiencia.expediente = expediente
            audiencia.save()
            messages.success(request, 'Evento de agenda registrado.')
            return redirect('expedientes:expediente_detail', pk=expediente.pk)
        return render(request, self.template_name, {'form': form, 'expediente': expediente})


class PersonalCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/personal_form.html'

    def get(self, request):
        form = PersonalForm()
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

    def post(self, request):
        form = PersonalForm(request.POST)
        if form.is_valid():
            personal = form.save()
            messages.success(request, f'Personal {personal.get_full_name()} registrado.')
            return redirect('expedientes:personal_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})


class PersonalListView(LoginRequiredMixin, ListView):
    model = Personal
    template_name = 'expedientes/personal_list.html'
    context_object_name = 'personal_list'
    paginate_by = 20

    def get_queryset(self):
        qs = Personal.objects.filter(deleted_at__isnull=True)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(nombres__icontains=q) | Q(apellidos__icontains=q) | Q(cedula__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class NotificacionMarcarLeidaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notif = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
        notif.leido = True
        notif.save(update_fields=['leido'])
        return redirect('expedientes:notificacion_list')


class CargoListView(LoginRequiredMixin, ListView):
    model = Cargo
    template_name = 'expedientes/cargo_list.html'
    context_object_name = 'cargos'
    paginate_by = 20
    def get_queryset(self):
        return Cargo.objects.filter(deleted_at__isnull=True)

class CargoCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/cargo_form.html'
    def get(self, request):
        form = CargoForm()
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})
    def post(self, request):
        form = CargoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cargo registrado exitosamente.')
            return redirect('expedientes:cargo_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

class CargoUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/cargo_form.html'
    def get(self, request, pk):
        obj = get_object_or_404(Cargo, pk=pk, deleted_at__isnull=True)
        form = CargoForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'cargo': obj})
    def post(self, request, pk):
        obj = get_object_or_404(Cargo, pk=pk, deleted_at__isnull=True)
        form = CargoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cargo actualizado.')
            return redirect('expedientes:cargo_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'cargo': obj})

class CargoDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(Cargo, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Cargo eliminado lógicamente.')
        return redirect('expedientes:cargo_list')


class MotivoListView(LoginRequiredMixin, ListView):
    model = Motivo
    template_name = 'expedientes/motivo_list.html'
    context_object_name = 'motivos'
    paginate_by = 20
    def get_queryset(self):
        return Motivo.objects.filter(deleted_at__isnull=True)

class MotivoCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/motivo_form.html'
    def get(self, request):
        form = MotivoForm()
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})
    def post(self, request):
        form = MotivoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motivo registrado.')
            return redirect('expedientes:motivo_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

class MotivoUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/motivo_form.html'
    def get(self, request, pk):
        obj = get_object_or_404(Motivo, pk=pk, deleted_at__isnull=True)
        form = MotivoForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})
    def post(self, request, pk):
        obj = get_object_or_404(Motivo, pk=pk, deleted_at__isnull=True)
        form = MotivoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motivo actualizado.')
            return redirect('expedientes:motivo_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})

class MotivoDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(Motivo, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Motivo eliminado.')
        return redirect('expedientes:motivo_list')


class TribunalListView(LoginRequiredMixin, ListView):
    model = Tribunal
    template_name = 'expedientes/tribunal_list.html'
    context_object_name = 'tribunales'
    paginate_by = 20
    def get_queryset(self):
        return Tribunal.objects.filter(deleted_at__isnull=True)

class TribunalCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/tribunal_form.html'
    def get(self, request):
        form = TribunalForm()
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})
    def post(self, request):
        form = TribunalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tribunal registrado.')
            return redirect('expedientes:tribunal_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

class TribunalUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/tribunal_form.html'
    def get(self, request, pk):
        obj = get_object_or_404(Tribunal, pk=pk, deleted_at__isnull=True)
        form = TribunalForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})
    def post(self, request, pk):
        obj = get_object_or_404(Tribunal, pk=pk, deleted_at__isnull=True)
        form = TribunalForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tribunal actualizado.')
            return redirect('expedientes:tribunal_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})

class TribunalDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(Tribunal, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Tribunal eliminado.')
        return redirect('expedientes:tribunal_list')


class NotificacionListView(LoginRequiredMixin, ListView):
    model = Notificacion
    template_name = 'expedientes/notificacion_list.html'
    context_object_name = 'notificaciones'
    paginate_by = 20
    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user, deleted_at__isnull=True).order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['no_leidas'] = Notificacion.objects.filter(usuario=self.request.user, leido=False, deleted_at__isnull=True).count()
        return context


# ─── Personal Update / Delete ────────────────────────────────────────────────

class PersonalUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/personal_form.html'
    def get(self, request, pk):
        obj = get_object_or_404(Personal, pk=pk, deleted_at__isnull=True)
        form = PersonalForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'personal': obj})
    def post(self, request, pk):
        obj = get_object_or_404(Personal, pk=pk, deleted_at__isnull=True)
        form = PersonalForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Personal actualizado.')
            return redirect('expedientes:personal_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'personal': obj})

class PersonalDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(Personal, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Personal eliminado lógicamente.')
        return redirect('expedientes:personal_list')


# ─── AudienciaAgenda List / Update / Delete ──────────────────────────────────

class AudienciaAgendaListView(LoginRequiredMixin, ListView):
    model = AudienciaAgenda
    template_name = 'expedientes/audiencia_list.html'
    context_object_name = 'audiencias'
    paginate_by = 20
    def get_queryset(self):
        return AudienciaAgenda.objects.filter(deleted_at__isnull=True).select_related('expediente')

class AudienciaAgendaUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/audiencia_form.html'
    def get(self, request, pk):
        obj = get_object_or_404(AudienciaAgenda, pk=pk, deleted_at__isnull=True)
        form = AudienciaAgendaForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'audiencia': obj})
    def post(self, request, pk):
        obj = get_object_or_404(AudienciaAgenda, pk=pk, deleted_at__isnull=True)
        form = AudienciaAgendaForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Audiencia actualizada.')
            return redirect('expedientes:audiencia_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'audiencia': obj})

class AudienciaAgendaDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(AudienciaAgenda, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Audiencia eliminada.')
        return redirect('expedientes:audiencia_list')


# ─── Calendario Interactivo (Lapsos y Agenda Procesal) ─────────────────────


class CalendarioLapsosView(LoginRequiredMixin, TemplateView):
    template_name = 'expedientes/calendario_lapsos.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['eventos'] = AudienciaAgenda.objects.filter(
            deleted_at__isnull=True
        ).select_related('expediente', 'usuario__personal').order_by('fecha_hora')
        return ctx


class CalendarioEventosJSONView(LoginRequiredMixin, View):
    def get(self, request):
        qs = AudienciaAgenda.objects.filter(deleted_at__isnull=True).select_related(
            'expediente', 'usuario__personal'
        )
        color_map = {
            'AUD': '#0d6efd',
            'LAPS': '#198754',
            'VENC': '#dc3545',
            'REC': '#6f42c1',
        }
        events = []
        for e in qs:
            events.append({
                'id': e.pk,
                'title': f'[{e.get_tipo_evento_display()}] {e.titulo}',
                'start': e.fecha_hora.isoformat(),
                'color': color_map.get(e.tipo_evento, '#6c757d'),
                'extendedProps': {
                    'codigo': e.tipo_evento,
                    'tipo': e.get_tipo_evento_display(),
                    'expediente': e.expediente.numero_expediente,
                    'lugar': e.lugar or '',
                    'descripcion': e.descripcion or '',
                    'abogado': str(e.usuario) if e.usuario else 'Sin asignar',
                    'alerta_email': e.alerta_email,
                    'alerta_sms': e.alerta_sms,
                    'notificado_30': e.notificado_30,
                    'notificado_60': e.notificado_60,
                    'notificado_90': e.notificado_90,
                },
            })
        return JsonResponse(events, safe=False)


# ─── LitigioContraparte CRUD ─────────────────────────────────────────────────

class LitigioContraparteListView(LoginRequiredMixin, ListView):
    model = LitigioContraparte
    template_name = 'expedientes/litigiocontraparte_list.html'
    context_object_name = 'contrapartes'
    paginate_by = 20
    def get_queryset(self):
        return LitigioContraparte.objects.filter(deleted_at__isnull=True).select_related('expediente')

class LitigioContraparteCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/litigiocontraparte_form.html'
    def get(self, request):
        form = LitigioContraparteForm()
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})
    def post(self, request):
        form = LitigioContraparteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contraparte registrada.')
            return redirect('expedientes:litigiocontraparte_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

class LitigioContraparteUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/litigiocontraparte_form.html'
    def get(self, request, pk):
        obj = get_object_or_404(LitigioContraparte, pk=pk, deleted_at__isnull=True)
        form = LitigioContraparteForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})
    def post(self, request, pk):
        obj = get_object_or_404(LitigioContraparte, pk=pk, deleted_at__isnull=True)
        form = LitigioContraparteForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contraparte actualizada.')
            return redirect('expedientes:litigiocontraparte_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})

class LitigioContraparteDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(LitigioContraparte, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Contraparte eliminada.')
        return redirect('expedientes:litigiocontraparte_list')


# ─── SustanciacionNotificacion CRUD ──────────────────────────────────────────

class SustanciacionNotificacionListView(LoginRequiredMixin, ListView):
    model = SustanciacionNotificacion
    template_name = 'expedientes/sustanciacionnotificacion_list.html'
    context_object_name = 'notificaciones_sust'
    paginate_by = 20
    def get_queryset(self):
        return SustanciacionNotificacion.objects.filter(deleted_at__isnull=True).select_related('expediente', 'personal')

class SustanciacionNotificacionCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/sustanciacionnotificacion_form.html'
    def get(self, request):
        form = SustanciacionNotificacionForm()
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})
    def post(self, request):
        form = SustanciacionNotificacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notificación de sustanciación registrada.')
            return redirect('expedientes:sustanciacionnotificacion_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

class SustanciacionNotificacionUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/sustanciacionnotificacion_form.html'
    def get(self, request, pk):
        obj = get_object_or_404(SustanciacionNotificacion, pk=pk, deleted_at__isnull=True)
        form = SustanciacionNotificacionForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})
    def post(self, request, pk):
        obj = get_object_or_404(SustanciacionNotificacion, pk=pk, deleted_at__isnull=True)
        form = SustanciacionNotificacionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notificación de sustanciación actualizada.')
            return redirect('expedientes:sustanciacionnotificacion_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})

class SustanciacionNotificacionDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(SustanciacionNotificacion, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Notificación de sustanciación eliminada.')
        return redirect('expedientes:sustanciacionnotificacion_list')


# ─── PersonaCargo CRUD ───────────────────────────────────────────────────────

class PersonaCargoListView(LoginRequiredMixin, ListView):
    model = PersonaCargo
    template_name = 'expedientes/personacargo_list.html'
    context_object_name = 'asignaciones'
    paginate_by = 20
    def get_queryset(self):
        return PersonaCargo.objects.filter(deleted_at__isnull=True).select_related('personal', 'cargo')


class PersonaCargoCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/personacargo_form.html'
    def get(self, request):
        form = PersonaCargoForm()
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})
    def post(self, request):
        form = PersonaCargoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asignación registrada.')
            return redirect('expedientes:personacargo_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})


class PersonaCargoUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/personacargo_form.html'
    def get(self, request, pk):
        obj = get_object_or_404(PersonaCargo, pk=pk, deleted_at__isnull=True)
        form = PersonaCargoForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})
    def post(self, request, pk):
        obj = get_object_or_404(PersonaCargo, pk=pk, deleted_at__isnull=True)
        form = PersonaCargoForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asignación actualizada.')
            return redirect('expedientes:personacargo_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar'})


class PersonaCargoDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(PersonaCargo, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Asignación eliminada.')
        return redirect('expedientes:personacargo_list')


# ─── Import / Export ─────────────────────────────────────────────────────────
# Cada export define (nombre_campo, etiqueta) para que al importar
# el mismo Excel, los encabezados coincidan exactamente.

CAMPOS_PERSONAL = [
    ('nombres', 'Nombres'), ('apellidos', 'Apellidos'),
    ('cedula', 'Cédula'), ('correo', 'Correo'),
    ('telefono', 'Teléfono'), ('direccion', 'Dirección'),
]
CAMPOS_CARGOS = [
    ('categoria', 'Categoría'), ('tipo', 'Tipo'),
    ('marco_legal', 'Marco Legal'), ('descripcion', 'Descripción'),
]
CAMPOS_MOTIVOS = [
    ('descripcion', 'Descripción'), ('tipo', 'Tipo'),
]
CAMPOS_TRIBUNALES = [
    ('nombre', 'Nombre'), ('tipo', 'Tipo'),
]
CAMPOS_ASIGNACIONES = [
    ('personal__get_full_name', 'Personal'), ('personal__cedula', 'Cédula'),
    ('cargo__descripcion', 'Cargo'), ('fecha_inicio', 'Inicio'),
    ('fecha_fin', 'Fin'), ('es_cargo_actual', 'Actual'),
]
CAMPOS_AUDIENCIAS = [
    ('titulo', 'Título'), ('tipo_evento', 'Tipo Evento'),
    ('fecha_hora', 'Fecha/Hora'), ('expediente__numero_expediente', 'Expediente'),
    ('lugar', 'Lugar'), ('descripcion', 'Descripción'),
]
CAMPOS_CONTRAPARTES = [
    ('expediente__numero_expediente', 'Expediente'),
    ('nombre_abogado', 'Nombre'), ('datos_contacto', 'Datos Contacto'),
]
CAMPOS_SUST_NOTIFICACION = [
    ('expediente__numero_expediente', 'Expediente'),
    ('personal__get_full_name', 'Personal'),
    ('fecha', 'Fecha'), ('hora', 'Hora'), ('lugar', 'Lugar'),
]
CAMPOS_EXPEDIENTE = [
    ('numero_expediente', 'N° Expediente'),
    ('tipo_modulo', 'Módulo'), ('estatus', 'Estatus'),
    ('personal__get_full_name', 'Personal'),
    ('personal__cedula', 'Cédula'),
    ('motivo__descripcion', 'Motivo'),
    ('fecha_registro', 'Fecha Registro'),
    ('fase_actual', 'Fase'), ('is_archivado', 'Archivado'),
]


class ExportarPersonalExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Personal.objects.filter(deleted_at__isnull=True)
        return ImportExportService.exportar_modelo_excel(qs, 'Personal', CAMPOS_PERSONAL)

class ExportarCargosExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Cargo.objects.filter(deleted_at__isnull=True)
        return ImportExportService.exportar_modelo_excel(qs, 'Cargos', CAMPOS_CARGOS)

class ExportarMotivosExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Motivo.objects.filter(deleted_at__isnull=True)
        return ImportExportService.exportar_modelo_excel(qs, 'Motivos', CAMPOS_MOTIVOS)

class ExportarTribunalesExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Tribunal.objects.filter(deleted_at__isnull=True)
        return ImportExportService.exportar_modelo_excel(qs, 'Tribunales', CAMPOS_TRIBUNALES)

class ExportarAsignacionesExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = PersonaCargo.objects.filter(deleted_at__isnull=True).select_related('personal', 'cargo')
        return ImportExportService.exportar_modelo_excel(qs, 'Asignaciones', CAMPOS_ASIGNACIONES)

class ExportarAudienciasExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = AudienciaAgenda.objects.filter(deleted_at__isnull=True).select_related('expediente')
        return ImportExportService.exportar_modelo_excel(qs, 'Audiencias', CAMPOS_AUDIENCIAS)

class ExportarLitigiosContraparteExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = LitigioContraparte.objects.filter(deleted_at__isnull=True).select_related('expediente')
        return ImportExportService.exportar_modelo_excel(qs, 'Contrapartes', CAMPOS_CONTRAPARTES)

class ExportarSustanciacionNotificacionExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = SustanciacionNotificacion.objects.filter(deleted_at__isnull=True).select_related('expediente', 'personal')
        return ImportExportService.exportar_modelo_excel(qs, 'Notif_Sustanciacion', CAMPOS_SUST_NOTIFICACION)

class ExportarExpedientesExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Expediente.objects.filter(deleted_at__isnull=True).select_related('personal', 'motivo')
        return ImportExportService.exportar_modelo_excel(qs, 'Expedientes', CAMPOS_EXPEDIENTE)

MAPA_IMPORTACION = {
    'Personal': (Personal, CAMPOS_PERSONAL),
    'Cargo': (Cargo, CAMPOS_CARGOS),
    'Motivo': (Motivo, CAMPOS_MOTIVOS),
    'Tribunal': (Tribunal, CAMPOS_TRIBUNALES),
    'PersonaCargo': (PersonaCargo, CAMPOS_ASIGNACIONES),
    'AudienciaAgenda': (AudienciaAgenda, CAMPOS_AUDIENCIAS),
    'LitigioContraparte': (LitigioContraparte, CAMPOS_CONTRAPARTES),
    'SustanciacionNotificacion': (SustanciacionNotificacion, CAMPOS_SUST_NOTIFICACION),
    'Expediente': (Expediente, CAMPOS_EXPEDIENTE),
    'Notificacion': (Notificacion, [
        ('mensaje', 'Mensaje'), ('tipo_alerta', 'Tipo Alerta'),
        ('leido', 'Leído'), ('fecha_creacion', 'Fecha Creación'),
    ]),
}

class ImportarExcelView(LoginRequiredMixin, View):
    def post(self, request, modelo):
        archivo = request.FILES.get('archivo')
        if not archivo:
            messages.error(request, 'Debe seleccionar un archivo Excel.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        info = MAPA_IMPORTACION.get(modelo)
        if not info:
            messages.error(request, f'Modelo "{modelo}" no soportado para importación.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        modelo_clase, campos = info
        try:
            creados, errores = ImportExportService.importar_modelo_excel(archivo, modelo_clase, campos)
            if creados:
                messages.success(request, f'Se importaron {creados} registros.')
            if errores:
                for e in errores[:3]:
                    messages.warning(request, e)
            if not creados and not errores:
                messages.info(request, 'No se encontraron datos nuevos para importar.')
        except Exception as e:
            messages.error(request, f'Error al importar: {e}')
        return redirect(request.META.get('HTTP_REFERER', '/'))


class ExpedienteArchivarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk, deleted_at__isnull=True)
        expediente.is_archivado = True
        expediente.save(update_fields=['is_archivado'])
        messages.success(request, f'Expediente {expediente.numero_expediente} archivado.')
        Actuacion.objects.create(
            content_object=expediente,
            descripcion=f"Expediente {expediente.numero_expediente} archivado por {request.user.get_full_name()}",
            usuario=request.user,
        )
        return redirect('expedientes:expediente_detail', pk=pk)


class ExpedienteDesarchivarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk, deleted_at__isnull=True)
        expediente.is_archivado = False
        expediente.save(update_fields=['is_archivado'])
        messages.success(request, f'Expediente {expediente.numero_expediente} desarchivado.')
        Actuacion.objects.create(
            content_object=expediente,
            descripcion=f"Expediente {expediente.numero_expediente} desarchivado por {request.user.get_full_name()}",
            usuario=request.user,
        )
        return redirect('expedientes:expediente_detail', pk=pk)


class SujetoProcesalListView(LoginRequiredMixin, ListView):
    model = SujetoProcesal
    template_name = 'expedientes/sujetoprocesal_list.html'
    context_object_name = 'sujetos'
    paginate_by = 20

    def get_queryset(self):
        qs = SujetoProcesal.objects.filter(deleted_at__isnull=True)
        tipo = self.request.GET.get('tipo', '').strip()
        if tipo:
            qs = qs.filter(tipo=tipo)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(models.Q(nombres__icontains=q) | models.Q(apellidos__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tipos'] = SujetoProcesal.TipoSujeto.choices
        ctx['tipo_filter'] = self.request.GET.get('tipo', '')
        ctx['search_query'] = self.request.GET.get('q', '')
        ctx['export_url'] = reverse_lazy('expedientes:exportar_sujetos_procesales')
        return ctx


class SujetoProcesalCreateView(LoginRequiredMixin, View):
    template_name = 'expedientes/sujetoprocesal_form.html'

    def get(self, request):
        form = SujetoProcesalForm()
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

    def post(self, request):
        form = SujetoProcesalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sujeto procesal registrado exitosamente.')
            return redirect('expedientes:sujetoprocesal_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})


class SujetoProcesalUpdateView(LoginRequiredMixin, View):
    template_name = 'expedientes/sujetoprocesal_form.html'

    def get(self, request, pk):
        obj = get_object_or_404(SujetoProcesal, pk=pk, deleted_at__isnull=True)
        form = SujetoProcesalForm(instance=obj)
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'sujeto': obj})

    def post(self, request, pk):
        obj = get_object_or_404(SujetoProcesal, pk=pk, deleted_at__isnull=True)
        form = SujetoProcesalForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sujeto procesal actualizado.')
            return redirect('expedientes:sujetoprocesal_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'sujeto': obj})


class SujetoProcesalDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(SujetoProcesal, pk=pk, deleted_at__isnull=True)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
        messages.success(request, 'Sujeto procesal eliminado lógicamente.')
        return redirect('expedientes:sujetoprocesal_list')


class ExportarSujetosProcesalesExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = SujetoProcesal.objects.filter(deleted_at__isnull=True)
        return ImportExportService.exportar_modelo_excel(
            qs, 'Sujetos Procesales',
            [
                ('get_tipo_display', 'Tipo'),
                ('nombres', 'Nombres'),
                ('apellidos', 'Apellidos'),
                ('cedula', 'Cédula'),
                ('telefono', 'Teléfono'),
                ('correo', 'Correo'),
                ('get_tribunal_display', 'Tribunal'),
            ]
        )
