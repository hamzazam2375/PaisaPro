from django.urls import path
from . import views

# Legacy URL patterns - minimal for health check
urlpatterns = [
    path('health/', views.health_check, name='health_check'),
]
