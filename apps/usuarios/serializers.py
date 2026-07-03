from rest_framework import serializers
from .models import Usuario, HistorialContrasena, BitacoraAuditoria

class UsuarioSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'usuario', 'full_name', 'cedula',
                  'correo', 'telefono', 'rol', 'foto_perfil', 'is_2fa_enabled',
                  'is_bloqueado', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_bloqueado', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return obj.get_full_name()

class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=16)
    password_repeat = serializers.CharField(write_only=True, min_length=16)

    class Meta:
        model = Usuario
        fields = ['usuario', 'personal', 'cedula', 'correo',
                  'telefono', 'rol', 'password', 'password_repeat']

    def validate(self, data):
        if data['password'] != data.pop('password_repeat'):
            raise serializers.ValidationError({"password_repeat": "Las contraseñas no coinciden."})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario

class BitacoraAuditoriaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = BitacoraAuditoria
        fields = '__all__'
        read_only_fields = ['hash_integridad', 'created_at']

    def get_usuario_nombre(self, obj):
        return obj.usuario.get_full_name() if obj.usuario else 'Anónimo'
