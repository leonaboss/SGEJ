from rest_framework import serializers
from .models import (
    Personal, Cargo, PersonaCargo, Motivo, Tribunal, Expediente,
    Actuacion, AudienciaAgenda, LitigioContraparte, Notificacion,
    SustanciacionNotificacion, SujetoProcesal
)

class PersonalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Personal
        fields = '__all__'
        read_only_fields = ['created_at']

    def get_full_name(self, obj):
        return obj.get_full_name()

class CargoSerializer(serializers.ModelSerializer):
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Cargo
        fields = '__all__'
        read_only_fields = ['created_at']

class PersonaCargoSerializer(serializers.ModelSerializer):
    personal_nombre = serializers.SerializerMethodField()
    cargo_nombre = serializers.SerializerMethodField()

    class Meta:
        model = PersonaCargo
        fields = '__all__'
        read_only_fields = ['created_at']

    def get_personal_nombre(self, obj):
        return obj.personal.get_full_name()
    def get_cargo_nombre(self, obj):
        return str(obj.cargo)

class MotivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motivo
        fields = '__all__'
        read_only_fields = ['created_at']

class TribunalSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Tribunal
        fields = '__all__'
        read_only_fields = ['created_at']

class ExpedienteListSerializer(serializers.ModelSerializer):
    tipo_modulo_display = serializers.CharField(source='get_tipo_modulo_display', read_only=True)
    estatus_display = serializers.CharField(source='get_estatus_display', read_only=True)
    personal_nombre = serializers.SerializerMethodField()
    usuario_nombre = serializers.SerializerMethodField()
    motivo_descripcion = serializers.SerializerMethodField()

    class Meta:
        model = Expediente
        fields = ['id', 'numero_expediente', 'tipo_modulo', 'tipo_modulo_display',
                  'estatus', 'estatus_display', 'personal_nombre', 'usuario_nombre',
                  'motivo_descripcion', 'fecha_registro', 'fase_actual',
                  'is_archivado', 'created_at']

    def get_personal_nombre(self, obj):
        return obj.personal.get_full_name() if obj.personal else '-'
    def get_usuario_nombre(self, obj):
        return obj.usuario.get_full_name() if obj.usuario else '-'
    def get_motivo_descripcion(self, obj):
        return str(obj.motivo) if obj.motivo else '-'

class ExpedienteDetalleSerializer(serializers.ModelSerializer):
    personal_detalle = PersonalSerializer(source='personal', read_only=True)
    motivo_detalle = MotivoSerializer(source='motivo', read_only=True)
    cargo_detalle = CargoSerializer(source='cargo', read_only=True)
    tribunal_detalle = TribunalSerializer(source='tribunal', read_only=True)
    usuario_nombre = serializers.SerializerMethodField()
    tipo_modulo_display = serializers.CharField(source='get_tipo_modulo_display', read_only=True)
    estatus_display = serializers.CharField(source='get_estatus_display', read_only=True)
    tema_filtro_display = serializers.CharField(source='get_tema_filtro_display', read_only=True)
    fase_actual_display = serializers.CharField(source='get_fase_actual_display', read_only=True)

    class Meta:
        model = Expediente
        fields = '__all__'

    def get_usuario_nombre(self, obj):
        return obj.usuario.get_full_name()

class ActuacionSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    documento_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Actuacion
        fields = '__all__'
        read_only_fields = ['created_at']

    def get_usuario_nombre(self, obj):
        return obj.usuario.get_full_name()
    def get_documento_nombre(self, obj):
        return obj.documento.nombre_original if obj.documento else None

class AudienciaAgendaSerializer(serializers.ModelSerializer):
    tipo_evento_display = serializers.CharField(source='get_tipo_evento_display', read_only=True)

    class Meta:
        model = AudienciaAgenda
        fields = '__all__'
        read_only_fields = ['created_at']

class LitigioContraparteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LitigioContraparte
        fields = '__all__'
        read_only_fields = ['created_at']

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = '__all__'
        read_only_fields = ['fecha_creacion']

class SustanciacionNotificacionSerializer(serializers.ModelSerializer):
    personal_nombre = serializers.SerializerMethodField()

    class Meta:
        model = SustanciacionNotificacion
        fields = '__all__'
        read_only_fields = ['created_at']

    def get_personal_nombre(self, obj):
        return obj.personal.get_full_name()


class SujetoProcesalSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    tribunal_display = serializers.CharField(source='get_tribunal_display', read_only=True)

    class Meta:
        model = SujetoProcesal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
