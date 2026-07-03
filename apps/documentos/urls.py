from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('', views.DocumentoListView.as_view(), name='documento_list'),
    path('subir/', views.DocumentoUploadView.as_view(), name='documento_upload'),
    path('<int:pk>/', views.DocumentoDetailView.as_view(), name='documento_detail'),
    path('<int:pk>/descargar/', views.DocumentoDownloadView.as_view(), name='documento_download'),
    path('<int:pk>/editar/', views.DocumentoUpdateView.as_view(), name='documento_update'),
    path('<int:pk>/eliminar/', views.DocumentoDeleteView.as_view(), name='documento_delete'),
    path('exportar/', views.ExportarDocumentosExcelView.as_view(), name='exportar_documentos'),
    path('importar/', views.ImportarDocumentosExcelView.as_view(), name='importar_documentos'),
    path('plantillas/', views.PlantillaListView.as_view(), name='plantilla_list'),
    path('plantillas/crear/', views.PlantillaCreateView.as_view(), name='plantilla_create'),
    path('plantillas/<int:pk>/editar/', views.PlantillaUpdateView.as_view(), name='plantilla_update'),
    path('plantillas/<int:pk>/eliminar/', views.PlantillaDeleteView.as_view(), name='plantilla_delete'),
    path('plantillas/<int:pk>/generar/', views.PlantillaGenerarView.as_view(), name='plantilla_generar'),
    path('plantillas/<int:pk>/variables/', views.PlantillaPreviewVariablesView.as_view(), name='plantilla_variables'),
]
