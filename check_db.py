import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgej_config.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SHOW TABLES")
    for row in cursor.fetchall():
        print(row[0])
