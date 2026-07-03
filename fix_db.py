import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgej_config.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    try:
        cursor.execute("CREATE TABLE `plantillas_documentos` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `nombre` varchar(200) NOT NULL UNIQUE, `descripcion` longtext NULL, `archivo_plantilla` varchar(100) NOT NULL, `tipo_salida` varchar(4) NOT NULL, `variables` json NOT NULL, `deleted_at` datetime(6) NULL, `created_at` datetime(6) NOT NULL, `updated_at` datetime(6) NOT NULL);")
        cursor.execute("ALTER TABLE `plantillas_documentos` ADD COLUMN `created_by` bigint NOT NULL;")
        cursor.execute("ALTER TABLE `plantillas_documentos` ADD CONSTRAINT `plantillas_documentos_created_by_fk_usuarios_id` FOREIGN KEY (`created_by`) REFERENCES `usuarios` (`id`);")
        print("Created plantillas_documentos")
    except Exception as e:
        print(f"Error creating plantillas_documentos: {e}")
