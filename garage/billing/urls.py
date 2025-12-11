from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('create/<int:case_id>/', views.invoice_create, name='invoice_create'),
    path('<int:pk>/download-pdf/', views.invoice_download_pdf, name='invoice_download_pdf'),
]
