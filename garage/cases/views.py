# garage/cases/views.py

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from .models import Case, StatusLog
from .forms import CaseCreateForm, FaultSelectionForm, CaseSearchForm, CaseUpdateStatusForm
from garage.catalog.models import FaultGroup, Fault
from garage.notifications.models import Notification


@login_required
def case_list(request):
    """
    Liste des dossiers de l'utilisateur avec recherche/filtrage
    BF30: Le client peut consulter la liste de ses dossiers
    """
    # Filtrer les dossiers selon le rôle
    if request.user.profile.role == 'CLIENT':
        cases = Case.objects.filter(client=request.user)
    else:
        # Gestionnaires et admins voient tous les dossiers
        cases = Case.objects.all()

    # Appliquer les filtres de recherche
    form = CaseSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        urgency = form.cleaned_data.get('urgency_level')

        if search:
            cases = cases.filter(
                Q(id__icontains=search) |
                Q(vehicle__brand__icontains=search) |
                Q(vehicle__model__icontains=search) |
                Q(vehicle__plate_number__icontains=search) |
                Q(description__icontains=search)
            )

        if status:
            cases = cases.filter(status=status)

        if urgency:
            cases = cases.filter(urgency_level=urgency)

    # Trier par date de création (plus récent en premier)
    cases = cases.select_related('client', 'vehicle').order_by('-created_at')

    context = {
        'cases': cases,
        'form': form,
        'is_client': request.user.profile.role == 'CLIENT',
    }

    return render(request, 'cases/case_list.html', context)


@login_required
def case_detail(request, pk):
    """
    Détail d'un dossier avec historique
    BF31: Visualisation complète du dossier
    """
    # Vérifier les permissions
    if request.user.profile.role == 'CLIENT':
        case = get_object_or_404(Case, pk=pk, client=request.user)
    else:
        case = get_object_or_404(Case, pk=pk)

    # Récupérer l'historique des changements de statut
    status_history = StatusLog.objects.filter(case=case).order_by('-changed_at')

    # Récupérer les pannes sélectionnées
    case_faults = case.faults.all()

    context = {
        'case': case,
        'status_history': status_history,
        'case_faults': case_faults,
        'is_client': request.user.profile.role == 'CLIENT',
        'can_add_faults': case.status == 'NOUVEAU' and request.user.profile.role == 'CLIENT',
    }

    return render(request, 'cases/case_detail.html', context)


@login_required
def case_create(request):
    """
    Créer un nouveau dossier de réparation
    BF20: Le client peut déclarer un problème
    """
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent créer des dossiers.")
        return redirect('cases:case_list')

    if request.method == 'POST':
        form = CaseCreateForm(request.POST, user=request.user)
        if form.is_valid():
            case = form.save()

            # Notifier les gestionnaires du nouveau dossier
            Notification.notify_managers_new_case(case)

            messages.success(request, f'Le dossier #{case.id} a été créé avec succès.')
            return redirect('cases:case_add_faults', pk=case.pk)
    else:
        form = CaseCreateForm(user=request.user)

    context = {
        'form': form,
    }

    return render(request, 'cases/case_create.html', context)


@login_required
def case_create_manager(request):
    """
    Créer un dossier en tant que gestionnaire pour un client existant.
    """
    if request.user.profile.role not in ['GESTIONNAIRE', 'ADMIN']:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    if request.method == 'POST':
        # Import local pour éviter dépendance circulaire si le formulaire est dans forms.py
        from .forms import CaseCreateManagerForm
        form = CaseCreateManagerForm(request.POST)
        if form.is_valid():
            case = form.save()
            messages.success(request, f"Le dossier #{case.id} pour {case.client.username} a été créé.")
            return redirect('cases:case_detail', pk=case.pk)
    else:
        from .forms import CaseCreateManagerForm
        form = CaseCreateManagerForm()

    context = {
        'form': form,
        'title': 'Nouveau Dossier (Mode Gestionnaire)'
    }
    return render(request, 'cases/case_create_manager.html', context)


@login_required
def case_add_faults(request, pk):
    """
    Ajouter des pannes au dossier depuis le catalogue
    BF21: Interface de sélection des pannes par groupes
    """
    # Seul le client propriétaire du dossier peut ajouter des pannes
    case = get_object_or_404(Case, pk=pk, client=request.user)

    # Vérifier que le dossier est encore au statut NOUVEAU
    if case.status != 'NOUVEAU':
        messages.error(request, "Vous ne pouvez plus modifier les pannes de ce dossier.")
        return redirect('cases:case_detail', pk=case.pk)

    if request.method == 'POST':
        form = FaultSelectionForm(request.POST, case=case)
        if form.is_valid():
            faults = form.cleaned_data.get('faults')
            if faults:
                # Ajouter les pannes sélectionnées
                case.faults.add(*faults)
                messages.success(request, f'{faults.count()} panne(s) ajoutée(s) au dossier.')

            # Rediriger selon l'action
            if 'add_more' in request.POST:
                return redirect('cases:case_add_faults', pk=case.pk)
            else:
                return redirect('cases:case_detail', pk=case.pk)
    else:
        form = FaultSelectionForm(case=case)

    # Récupérer tous les groupes de pannes
    fault_groups = FaultGroup.objects.all().order_by('order')

    # Récupérer les pannes déjà sélectionnées
    selected_faults = case.faults.all()

    context = {
        'case': case,
        'form': form,
        'fault_groups': fault_groups,
        'selected_faults': selected_faults,
    }

    return render(request, 'cases/case_add_faults.html', context)


@login_required
def case_remove_fault(request, pk, fault_id):
    """
    Retirer une panne du dossier
    """
    if request.method != 'POST':
        messages.error(request, "Action non autorisée.")
        return redirect('cases:case_detail', pk=pk)

    case = get_object_or_404(Case, pk=pk, client=request.user)

    if case.status != 'NOUVEAU':
        messages.error(request, "Vous ne pouvez plus modifier les pannes de ce dossier.")
        return redirect('cases:case_detail', pk=case.pk)

    fault = get_object_or_404(Fault, pk=fault_id)
    case.faults.remove(fault)

    messages.success(request, f'La panne "{fault.name}" a été retirée du dossier.')
    
    # Rediriger vers la page précédente si possible, sinon détail
    referer = request.META.get('HTTP_REFERER', '')
    if 'add-faults' in referer:
        return redirect('cases:case_add_faults', pk=case.pk)
    return redirect('cases:case_detail', pk=case.pk)


@login_required
def get_faults_by_group(request, group_id):
    """
    API endpoint pour récupérer les pannes d'un groupe (AJAX)
    """
    faults = Fault.objects.filter(group_id=group_id, is_active=True).values(
        'id', 'name', 'description', 'labor_hours', 'parts_cost'
    )
    return JsonResponse(list(faults), safe=False)


@login_required
def case_update_status(request, pk):
    """
    Mettre à jour le statut d'un dossier (gestionnaire uniquement)
    BF50: Le gestionnaire peut faire évoluer le statut du dossier
    """
    if request.user.profile.role not in ['GESTIONNAIRE', 'ADMIN']:
        messages.error(request, "Vous n'avez pas les permissions pour cette action.")
        return redirect('cases:case_detail', pk=pk)

    case = get_object_or_404(Case, pk=pk)

    if request.method == 'POST':
        form = CaseUpdateStatusForm(request.POST, instance=case)
        if form.is_valid():
            old_status = case.status
            new_case = form.save()

            # Créer l'entrée dans l'historique
            StatusLog.objects.create(
                case=new_case,
                old_status=old_status,
                new_status=new_case.status,
                changed_by=request.user
            )

            # Créer une notification pour le client
            Notification.create_for_case_status_change(new_case, new_case.status)

            messages.success(request, f'Le statut du dossier a été mis à jour.')
            return redirect('cases:case_detail', pk=case.pk)
    else:
        form = CaseUpdateStatusForm(instance=case)

    context = {
        'case': case,
        'form': form,
    }

    return render(request, 'cases/case_update_status.html', context)
