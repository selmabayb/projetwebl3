# garage/views.py

from django.shortcuts import render


def home(request):
    """Page d'accueil du site"""
    return render(request, 'home.html')
