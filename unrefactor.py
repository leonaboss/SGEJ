import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w') as f:
        f.write(content)

apps_dir = '/home/matrix/SGEJ/apps'

# views.py
views_path = os.path.join(apps_dir, 'expedientes/views.py')
replace_in_file(views_path, [
    ("modulo__nombre='DESP'", "tipo_modulo='DESP'"),
    ("modulo__nombre='INSP'", "tipo_modulo='INSP'"),
    ("modulo__nombre='OFIC'", "tipo_modulo='OFIC'"),
    ("modulo__nombre='CONT'", "tipo_modulo='CONT'"),
    ("modulo__nombre='LITI'", "tipo_modulo='LITI'"),
    ("modulo__nombre='SUST'", "tipo_modulo='SUST'"),
    ("modulo__nombre='IND'", "tipo_modulo='IND'"),
    ("modulo__nombre=tipo", "tipo_modulo=tipo"),
    ("expediente.modulo.nombre", "expediente.tipo_modulo"),
])

# forms.py
forms_path = os.path.join(apps_dir, 'expedientes/forms.py')
replace_in_file(forms_path, [
    ("'modulo'", "'tipo_modulo'"),
])

# admin.py
admin_path = os.path.join(apps_dir, 'expedientes/admin.py')
replace_in_file(admin_path, [
    ("'modulo'", "'tipo_modulo'"),
])

# tests.py
tests_path1 = os.path.join(apps_dir, 'expedientes/tests.py')
tests_path2 = os.path.join(apps_dir, 'documentos/tests.py')
for path in [tests_path1, tests_path2]:
    if os.path.exists(path):
        replace_in_file(path, [
            ("modulo=", "tipo_modulo="), 
        ])

# services.py
services_path = os.path.join(apps_dir, 'expedientes/services.py')
replace_in_file(services_path, [
    ("modulo.get_nombre_display()", "get_tipo_modulo_display()"),
])

# serializers.py
serializers_path = os.path.join(apps_dir, 'expedientes/serializers.py')
replace_in_file(serializers_path, [
    ("source='modulo.get_nombre_display'", "source='get_tipo_modulo_display'"),
    ("'modulo'", "'tipo_modulo'"),
])

# api.py
api_path = os.path.join(apps_dir, 'expedientes/api.py')
replace_in_file(api_path, [
    ("'modulo__nombre'", "'tipo_modulo'"),
])
