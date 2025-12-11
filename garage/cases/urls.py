# garage/cases/urls.py

from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    path('', views.case_list, name='case_list'),
    path('<int:pk>/', views.case_detail, name='case_detail'),
    path('create/', views.case_create, name='case_create'),
    path('create/manager/', views.case_create_manager, name='case_create_manager'),
    path('<int:pk>/add-faults/', views.case_add_faults, name='case_add_faults'),
    path('<int:pk>/remove-fault/<int:fault_id>/', views.case_remove_fault, name='case_remove_fault'),
    path('<int:pk>/update-status/', views.case_update_status, name='case_update_status'),
    path('api/faults-by-group/<int:group_id>/', views.get_faults_by_group, name='get_faults_by_group'),
]
