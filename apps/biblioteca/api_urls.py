from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import ModuloBibliotecaViewSet

router = DefaultRouter()
router.register(r'normativas', ModuloBibliotecaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]