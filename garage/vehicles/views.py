# garage/vehicles/views.py

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Vehicle, VehicleHistory
from .forms import VehicleForm, VehicleSearchForm


@login_required
def vehicle_list(request):
    """
    Liste des véhicules de l'utilisateur connecté avec recherche/filtrage
    BF10: Le client peut lister ses véhicules
    """
    # Seuls les clients peuvent accéder à leurs véhicules
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients ont accès à la liste des véhicules.")
        from django.shortcuts import redirect
        return redirect('accounts:dashboard')

    # Récupérer uniquement les véhicules de l'utilisateur connecté
    vehicles = Vehicle.objects.filter(owner=request.user)

    # Appliquer les filtres de recherche
    if request.GET:
        form = VehicleSearchForm(request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            fuel_type = form.cleaned_data.get('fuel_type')
            is_active = form.cleaned_data.get('is_active')

            if search:
                vehicles = vehicles.filter(
                    Q(brand__icontains=search) |
                    Q(model__icontains=search) |
                    Q(plate_number__icontains=search) |
                    Q(nickname__icontains=search)
                )

            if fuel_type:
                vehicles = vehicles.filter(fuel_type=fuel_type)

            if is_active == 'true':
                vehicles = vehicles.filter(is_active=True)
            elif is_active == 'false':
                vehicles = vehicles.filter(is_active=False)
            # Si is_active est vide (''), on affiche tous les véhicules (comportement par défaut du filtre "Tous")
    else:
        # Si aucun paramètre n'est fourni, on initialise le formulaire avec "Actifs seulement"
        form = VehicleSearchForm(initial={'is_active': 'true'})
        # Et on filtre par défaut pour ne montrer que les actifs
        vehicles = vehicles.filter(is_active=True)

    # Trier par date de création (plus récent en premier)
    vehicles = vehicles.order_by('-created_at')

    context = {
        'vehicles': vehicles,
        'form': form,
        'total_count': Vehicle.objects.filter(owner=request.user).count(),
        'active_count': Vehicle.objects.filter(owner=request.user, is_active=True).count(),
    }

    return render(request, 'vehicles/vehicle_list.html', context)


@login_required
def vehicle_detail(request, pk):
    """
    Détail d'un véhicule avec son historique
    BF10: Visualisation complète des informations du véhicule
    """
    # Seuls les clients peuvent voir leurs véhicules
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent consulter les détails de leurs véhicules.")
        return redirect('accounts:dashboard')

    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)

    # Récupérer l'historique du véhicule
    history = VehicleHistory.objects.filter(vehicle=vehicle).order_by('-event_date')

    context = {
        'vehicle': vehicle,
        'history': history,
    }

    return render(request, 'vehicles/vehicle_detail.html', context)


@login_required
def vehicle_create(request):
    """
    Créer un nouveau véhicule
    BF10: Le client peut créer un ou plusieurs véhicules
    """
    # Seuls les clients peuvent créer des véhicules
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent ajouter des véhicules.")
        return redirect('vehicles:vehicle_list')

    if request.method == 'POST':
        form = VehicleForm(request.POST, user=request.user)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f'Le véhicule {vehicle.get_identifier()} a été créé avec succès.')
            return redirect('vehicles:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm(user=request.user)

    context = {
        'form': form,
        'action': 'Créer',
    }

    return render(request, 'vehicles/vehicle_form.html', context)


@login_required
def vehicle_update(request, pk):
    """
    Modifier un véhicule existant
    BF10: Le client peut modifier les informations de son véhicule
    """
    # Seuls les clients peuvent modifier des véhicules
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent modifier des véhicules.")
        return redirect('vehicles:vehicle_list')

    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle, user=request.user)
        if form.is_valid():
            # Stocker les anciennes valeurs pour l'historique
            old_mileage = vehicle.mileage

            vehicle = form.save()

            # Créer une entrée d'historique si le kilométrage a changé
            if 'mileage' in form.changed_data and vehicle.mileage != old_mileage:
                VehicleHistory.objects.create(
                    vehicle=vehicle,
                    event_type='MODIFICATION',
                    description=f'Mise à jour du kilométrage: {old_mileage} km → {vehicle.mileage} km'
                )

            messages.success(request, f'Le véhicule {vehicle.get_identifier()} a été mis à jour.')
            return redirect('vehicles:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle, user=request.user)

    context = {
        'form': form,
        'vehicle': vehicle,
        'action': 'Modifier',
    }

    return render(request, 'vehicles/vehicle_form.html', context)


@login_required
def vehicle_delete(request, pk):
    """
    Désactiver un véhicule (soft delete)
    BF10: Le client peut supprimer (désactiver) un véhicule
    """
    # Seuls les clients peuvent supprimer leurs véhicules
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent supprimer des véhicules.")
        return redirect('vehicles:vehicle_list')

    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)

    if request.method == 'POST':
        vehicle.is_active = False
        vehicle.save()

        # Créer une entrée d'historique
        VehicleHistory.objects.create(
            vehicle=vehicle,
            event_type='DELETE',
            description=f'Véhicule désactivé par {request.user.get_full_name() or request.user.username}'
        )

        messages.success(request, f'Le véhicule {vehicle.get_identifier()} a été désactivé.')
        return redirect('vehicles:vehicle_list')

    context = {
        'vehicle': vehicle,
    }

    return render(request, 'vehicles/vehicle_confirm_delete.html', context)


@login_required
def vehicle_activate(request, pk):
    """
    Réactiver un véhicule désactivé
    """
    # Seuls les clients peuvent réactiver leurs véhicules
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent réactiver des véhicules.")
        return redirect('accounts:dashboard')

    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)

    if request.method == 'POST':
        vehicle.is_active = True
        vehicle.save()

        # Créer une entrée d'historique
        VehicleHistory.objects.create(
            vehicle=vehicle,
            event_type='ACTIVATION',
            description=f'Véhicule réactivé par {request.user.get_full_name() or request.user.username}'
        )

        messages.success(request, f'Le véhicule {vehicle.get_identifier()} a été réactivé.')
        return redirect('vehicles:vehicle_detail', pk=vehicle.pk)

    return redirect('vehicles:vehicle_list')
