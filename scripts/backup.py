#!/usr/bin/env python
"""
Script de respaldo diario SGEJ.
Exporta la base de datos a SQL, Excel y CSV.
Ejecutar con: python scripts/backup.py
"""
import os
import sys
import subprocess
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

DB_NAME = os.environ.get('DB_NAME', 'sgej_juridico')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '123456')
DB_HOST = os.environ.get('DB_HOST', 'localhost')

def export_sql():
    sql_path = BACKUP_DIR / f'sgej_backup_{TIMESTAMP}.sql'
    cmd = [
        'mysqldump',
        f'--user={DB_USER}',
        f'--password={DB_PASSWORD}',
        f'--host={DB_HOST}',
        '--single-transaction',
        '--routines',
        '--triggers',
        DB_NAME,
    ]
    with open(sql_path, 'w') as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)
    print(f'SQL backup: {sql_path}')

def export_excel():
    excel_path = BACKUP_DIR / f'sgej_backup_{TIMESTAMP}.xlsx'
    sys.path.insert(0, str(BASE_DIR))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgej_config.settings')
    import django
    django.setup()
    from apps.expedientes.services import ExportacionService
    from apps.expedientes.models import Expediente, AudienciaAgenda
    from openpyxl import Workbook
    wb = Workbook()
    ws_exp = wb.active
    ws_exp.title = 'Expedientes'
    encabezados = ['N° Expediente', 'Módulo', 'Estatus', 'Personal', 'Cédula',
                   'Motivo', 'Fecha Registro', 'Fase', 'Archivado']
    ws_exp.append(encabezados)
    for exp in Expediente.objects.filter(deleted_at__isnull=True).select_related('personal', 'motivo'):
        ws_exp.append([
            exp.numero_expediente,
            exp.get_tipo_modulo_display(),
            exp.get_estatus_display(),
            exp.personal.get_full_name() if exp.personal else '-',
            exp.personal.cedula if exp.personal else '-',
            str(exp.motivo) if exp.motivo else '-',
            str(exp.fecha_registro) if exp.fecha_registro else '-',
            exp.get_fase_actual_display() if exp.fase_actual else '-',
            'Sí' if exp.is_archivado else 'No',
        ])
    ws_aud = wb.create_sheet('Audiencias')
    ws_aud.append(['Título', 'Tipo Evento', 'Fecha/Hora', 'Expediente', 'Descripción'])
    for aud in AudienciaAgenda.objects.filter(deleted_at__isnull=True).select_related('expediente'):
        ws_aud.append([
            aud.titulo,
            aud.get_tipo_evento_display(),
            aud.fecha_hora.strftime('%d/%m/%Y %H:%M'),
            aud.expediente.numero_expediente,
            aud.descripcion or '',
        ])
    wb.save(str(excel_path))
    print(f'Excel backup: {excel_path}')

if __name__ == '__main__':
    export_sql()
    export_excel()
    print(f'Backup completado en: {BACKUP_DIR}')
