# garage/appointments/urls.py

from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='appointment_list'),
    path('<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('create/<int:case_id>/', views.appointment_create, name='appointment_create'),
    path('<int:pk>/modify/', views.appointment_modify, name='appointment_modify'),
    path('<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),

    # API endpoint pour récupérer les créneaux disponibles
    path('api/available-slots/', views.get_available_slots, name='get_available_slots'),
]
