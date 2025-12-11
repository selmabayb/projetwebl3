# garage/appointments/views.py

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
from datetime import datetime, timedelta

from .models import Appointment, AppointmentSlot
from .forms import AppointmentCreateForm, AppointmentModifyForm, AppointmentCancelForm
from garage.cases.models import Case
from garage.notifications.models import Notification


@login_required
def appointment_list(request):
    """Liste des rendez-vous"""
    # Filtrer selon le rôle
    if request.user.profile.role == 'CLIENT':
        appointments = Appointment.objects.filter(case__client=request.user)
        is_client = True
    else:
        appointments = Appointment.objects.all()
        is_client = False

    appointments = appointments.select_related('case', 'case__client', 'case__vehicle').order_by('date', 'start_time')

    # Séparer les RDV à venir et passés
    today = timezone.now().date()
    upcoming = appointments.filter(date__gte=today, is_cancelled=False)
    past = appointments.filter(date__lt=today) | appointments.filter(is_cancelled=True)

    context = {
        'upcoming_appointments': upcoming,
        'past_appointments': past,
        'is_client': is_client,
    }

    return render(request, 'appointments/appointment_list.html', context)


@login_required
def appointment_detail(request, pk):
    """Détail d'un rendez-vous"""
    # Vérifier les permissions
    if request.user.profile.role == 'CLIENT':
        appointment = get_object_or_404(Appointment, pk=pk, case__client=request.user)
    else:
        appointment = get_object_or_404(Appointment, pk=pk)

    context = {
        'appointment': appointment,
        'is_client': request.user.profile.role == 'CLIENT',
        'can_modify': appointment.can_be_modified(),
        'can_cancel': appointment.can_be_cancelled(),
    }

    return render(request, 'appointments/appointment_detail.html', context)


@login_required
@transaction.atomic
def appointment_create(request, case_id):
    """Créer un rendez-vous pour un dossier (client uniquement)"""
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent réserver des rendez-vous.")
        return redirect('cases:case_list')

    case = get_object_or_404(Case, pk=case_id, client=request.user)

    # Vérifier que le dossier est au statut DEVIS_ACCEPTE
    if case.status != 'DEVIS_ACCEPTE':
        messages.error(request, "Vous devez d'abord accepter le devis avant de réserver un rendez-vous.")
        return redirect('cases:case_detail', pk=case.pk)

    # Supprimer les rendez-vous annulés existants pour ce dossier
    # (nécessaire car case.appointment est une relation OneToOneField)
    Appointment.objects.filter(case=case, is_cancelled=True).delete()

    # Vérifier qu'un RDV actif n'existe pas déjà
    if Appointment.objects.filter(case=case, is_cancelled=False).exists():
        messages.error(request, "Un rendez-vous actif existe déjà pour ce dossier.")
        return redirect('cases:case_detail', pk=case.pk)

    if request.method == 'POST':
        form = AppointmentCreateForm(request.POST, case=case)
        if form.is_valid():
            appointment = form.save()

            # Create notification for client (RDV_CONFIRME)
            Notification.create_for_case_status_change(case, 'RDV_CONFIRME')

            # Notifier les gestionnaires du nouveau RDV
            Notification.notify_managers_appointment_created(appointment)

            # Envoyer un email de confirmation au client
            try:
                from garage.utils.email import send_appointment_confirmed_email
                send_appointment_confirmed_email(appointment)
            except Exception as e:
                # Log l'erreur mais ne bloque pas le processus
                print(f"Erreur lors de l'envoi de l'email: {e}")

            messages.success(request, f'Votre rendez-vous a été réservé pour le {appointment.date.strftime("%d/%m/%Y")} à {appointment.start_time.strftime("%H:%M")}.')
            return redirect('appointments:appointment_detail', pk=appointment.pk)
    else:
        form = AppointmentCreateForm(case=case)

    context = {
        'form': form,
        'case': case,
    }

    return render(request, 'appointments/appointment_create.html', context)


@login_required
@transaction.atomic
def appointment_modify(request, pk):
    """Modifier un rendez-vous existant"""
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent modifier leurs rendez-vous.")
        return redirect('appointments:appointment_list')

    appointment = get_object_or_404(Appointment, pk=pk, case__client=request.user)

    if not appointment.can_be_modified():
        messages.error(request, "Ce rendez-vous ne peut plus être modifié (moins de 24h avant l'heure prévue ou déjà annulé).")
        return redirect('appointments:appointment_detail', pk=appointment.pk)

    if request.method == 'POST':
        form = AppointmentModifyForm(request.POST, instance=appointment)
        if form.is_valid():
            appointment = form.save()

            # Notifier les gestionnaires de la modification
            Notification.notify_managers_appointment_modified(appointment)

            messages.success(request, f'Votre rendez-vous a été modifié. Nouvelle date : {appointment.date.strftime("%d/%m/%Y")} à {appointment.start_time.strftime("%H:%M")}.')
            return redirect('appointments:appointment_detail', pk=appointment.pk)
    else:
        form = AppointmentModifyForm(instance=appointment)

    context = {
        'form': form,
        'appointment': appointment,
    }

    return render(request, 'appointments/appointment_modify.html', context)


@login_required
@transaction.atomic
def appointment_cancel(request, pk):
    """Annuler un rendez-vous"""
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent annuler leurs rendez-vous.")
        return redirect('appointments:appointment_list')

    appointment = get_object_or_404(Appointment, pk=pk, case__client=request.user)

    if not appointment.can_be_cancelled():
        messages.error(request, "Ce rendez-vous ne peut plus être annulé (moins de 24h avant l'heure prévue ou déjà annulé).")
        return redirect('appointments:appointment_detail', pk=appointment.pk)

    if request.method == 'POST':
        form = AppointmentCancelForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data.get('reason', '')
            appointment.cancel(reason)

            # Notifier les gestionnaires de l'annulation
            Notification.notify_managers_appointment_cancelled(appointment)

            # Envoyer un email de confirmation d'annulation au client
            try:
                from garage.utils.email import send_appointment_cancelled_email
                send_appointment_cancelled_email(appointment)
            except Exception as e:
                # Log l'erreur mais ne bloque pas le processus
                print(f"Erreur lors de l'envoi de l'email: {e}")

            messages.success(request, 'Votre rendez-vous a été annulé.')
            return redirect('cases:case_detail', pk=appointment.case.pk)
    else:
        form = AppointmentCancelForm()

    context = {
        'form': form,
        'appointment': appointment,
    }

    return render(request, 'appointments/appointment_cancel.html', context)


@login_required
def get_available_slots(request):
    """
    API endpoint pour récupérer les créneaux disponibles pour une date donnée
    Utilisé par AJAX dans le formulaire de réservation
    """
    date_str = request.GET.get('date')

    if not date_str:
        return JsonResponse({'error': 'Date requise'}, status=400)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Format de date invalide'}, status=400)

    # Récupérer le jour de la semaine (0 = lundi, 6 = dimanche)
    weekday = date.weekday()

    # Récupérer les créneaux récurrents pour ce jour
    recurring_slots = AppointmentSlot.objects.filter(
        is_recurring=True,
        weekday=weekday,
        is_available=True
    )

    # Récupérer les créneaux ponctuels pour cette date
    specific_slots = AppointmentSlot.objects.filter(
        is_recurring=False,
        date=date,
        is_available=True
    )

    # Vérifier les exceptions (jours fériés, fermetures)
    has_exception = AppointmentSlot.objects.filter(
        date=date,
        is_exception=True
    ).exists()

    if has_exception:
        return JsonResponse({'slots': [], 'message': 'Le garage est fermé ce jour-là.'})

    # Combiner les créneaux
    all_slots = list(recurring_slots) + list(specific_slots)

    # Filtrer les créneaux déjà réservés
    available_slots = []
    for slot in all_slots:
        # Vérifier si le créneau est déjà réservé
        is_booked = Appointment.objects.filter(
            date=date,
            start_time=slot.start_time,
            is_cancelled=False
        ).exists()

        if not is_booked:
            available_slots.append({
                'id': slot.id,
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'display': f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
            })

    # Trier par heure de début
    available_slots.sort(key=lambda x: x['start_time'])

    return JsonResponse({'slots': available_slots})
