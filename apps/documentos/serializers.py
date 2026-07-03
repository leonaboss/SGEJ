from rest_framework import serializers
from .models import Documento, DocumentoFirma

class DocumentoSerializer(serializers.ModelSerializer):
    created_by_nombre = serializers.SerializerMethodField()
    expediente_numero = serializers.SerializerMethodField()
    normativa_citada_titulo = serializers.SerializerMethodField()

    class Meta:
        model = Documento
        fields = '__all__'
        read_only_fields = ['hash_sha256', 'iv_cifrado', 'qr_code_content', 'version', 'created_at']

    def get_created_by_nombre(self, obj):
        return obj.created_by.get_full_name()
    def get_expediente_numero(self, obj):
        return obj.expediente.numero_expediente if obj.expediente else None
    def get_normativa_citada_titulo(self, obj):
        return obj.normativa_citada.titulo if obj.normativa_citada else None

class DocumentoFirmaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = DocumentoFirma
        fields = '__all__'
        read_only_fields = ['fecha_firma']

    def get_usuario_nombre(self, obj):
        return obj.usuario.get_full_name()
