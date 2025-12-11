# garage/quotes/urls.py

from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    path('', views.quote_list, name='quote_list'),
    path('<int:pk>/', views.quote_detail, name='quote_detail'),
    path('create/<int:case_id>/', views.quote_create, name='quote_create'),
    path('<int:pk>/edit-lines/', views.quote_edit_lines, name='quote_edit_lines'),
    path('<int:pk>/validate/', views.quote_validate, name='quote_validate'),
    path('<int:pk>/accept/', views.quote_accept, name='quote_accept'),
    path('<int:pk>/refuse/', views.quote_refuse, name='quote_refuse'),
    path('<int:pk>/download-pdf/', views.quote_download_pdf, name='quote_download_pdf'),
]
