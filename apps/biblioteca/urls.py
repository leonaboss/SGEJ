from django.urls import path
from . import views

app_name = 'biblioteca'

urlpatterns = [
    path('', views.BibliotecaListView.as_view(), name='lista'),
    path('crear/', views.BibliotecaCreateView.as_view(), name='crear'),
    path('editar/<int:pk>/', views.BibliotecaUpdateView.as_view(), name='editar'),
    path('eliminar/<int:pk>/', views.BibliotecaDeleteView.as_view(), name='eliminar'),
    path('exportar/', views.ExportarBibliotecaExcelView.as_view(), name='exportar'),
    path('importar/', views.ImportarBibliotecaExcelView.as_view(), name='importar'),
]
