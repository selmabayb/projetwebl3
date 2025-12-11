from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import UserRegistrationForm
from garage.vehicles.models import Vehicle
from garage.quotes.models import Quote
from garage.appointments.models import Appointment


def register(request):
    """
    Enregistrement d'un nouvel utilisateur
    BF1: Inscription avec profil automatique
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    """
    Tableau de bord personnalisé selon le rôle
    BF2: Dashboard avec statistiques client/gestionnaire

    Optimisé avec select_related pour éviter les N+1 queries
    """
    user = request.user
    role = user.profile.role

    stats = {
        'vehicle_count': 0,
        'pending_quote_count': 0,
        'upcoming_appointment_count': 0,
    }

    today = timezone.now().date()

    if role in ['GESTIONNAIRE', 'ADMIN']:
        # Stats globales pour les gestionnaires (optimisées)
        stats['vehicle_count'] = Vehicle.objects.count()

        # Devis en attente de validation gestionnaire
        stats['pending_quote_count'] = Quote.objects.filter(
            is_validated_by_manager=False
        ).count()

        # Tous les RDV à venir (optimisé avec select_related)
        stats['upcoming_appointment_count'] = Appointment.objects.select_related(
            'case', 'case__client'
        ).filter(
            date__gte=today,
            is_cancelled=False
        ).count()
    else:
        # Stats personnelles pour les clients (optimisées)
        stats['vehicle_count'] = Vehicle.objects.filter(owner=user).count()

        # Devis validés par le manager mais pas encore répondus par le client
        stats['pending_quote_count'] = Quote.objects.select_related('case').filter(
            case__client=user,
            is_validated_by_manager=True,
            is_accepted_by_client=False,
            is_refused_by_client=False
        ).count()

        # RDV à venir du client (optimisé avec select_related)
        stats['upcoming_appointment_count'] = Appointment.objects.select_related(
            'case'
        ).filter(
            case__client=user,
            date__gte=today,
            is_cancelled=False
        ).count()

    return render(request, 'dashboard.html', {
        'user': user,
        'stats': stats
    })
