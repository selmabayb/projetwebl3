# garage/quotes/views.py

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from .models import Quote, QuoteLine
from .forms import QuoteCreateForm, QuoteLineForm, QuoteAcceptForm, QuoteRefuseForm, QuoteValidateForm
from garage.cases.models import Case
from garage.catalog.models import SystemSettings
from garage.notifications.models import Notification


def get_quote_status(quote):
    """Helper function to determine quote status"""
    if quote.is_refused_by_client:
        return 'REFUSED'
    elif quote.is_accepted_by_client:
        return 'ACCEPTED'
    elif quote.is_validated_by_manager:
        if quote.is_expired():
            return 'EXPIRED'
        return 'EMITTED'
    else:
        return 'DRAFT'


@login_required
def quote_list(request):
    """Liste des devis"""
    # Filtrer selon le rôle
    if request.user.profile.role == 'CLIENT':
        quotes = Quote.objects.filter(case__client=request.user)
        is_client = True
    else:
        quotes = Quote.objects.all()
        is_client = False

    quotes = quotes.select_related('case', 'case__client', 'case__vehicle').order_by('-created_at')

    # Calculer les statistiques
    stats = {
        'draft': quotes.filter(is_validated_by_manager=False).count(),
        'emitted': quotes.filter(is_validated_by_manager=True, is_accepted_by_client=False, is_refused_by_client=False).count(),
        'accepted': quotes.filter(is_accepted_by_client=True).count(),
        'refused': quotes.filter(is_refused_by_client=True).count(),
    }

    context = {
        'quotes': quotes,
        'is_client': is_client,
        'stats': stats,
    }

    return render(request, 'quotes/quote_list.html', context)


@login_required
def quote_detail(request, pk):
    """Détail d'un devis avec toutes les lignes"""
    # Vérifier les permissions
    if request.user.profile.role == 'CLIENT':
        quote = get_object_or_404(Quote, pk=pk, case__client=request.user)
    else:
        quote = get_object_or_404(Quote, pk=pk)

    # Récupérer les lignes du devis
    quote_lines = quote.lines.all()

    # Déterminer le statut
    status = get_quote_status(quote)

    context = {
        'quote': quote,
        'quote_lines': quote_lines,
        'is_client': request.user.profile.role == 'CLIENT',
        'status': status,
    }

    return render(request, 'quotes/quote_detail.html', context)


@login_required
@transaction.atomic
def quote_create(request, case_id):
    """Créer un devis pour un dossier (gestionnaire uniquement)"""
    if request.user.profile.role not in ['GESTIONNAIRE', 'ADMIN']:
        messages.error(request, "Vous n'avez pas les permissions pour créer un devis.")
        return redirect('cases:case_list')

    case = get_object_or_404(Case, pk=case_id)

    # Vérifier que le dossier est au statut NOUVEAU
    if case.status != 'NOUVEAU':
        messages.error(request, "Un devis ne peut être créé que pour un dossier au statut NOUVEAU.")
        return redirect('cases:case_detail', pk=case.pk)

    # Vérifier qu'un devis n'existe pas déjà
    if Quote.objects.filter(case=case).exists():
        messages.error(request, "Un devis existe déjà pour ce dossier.")
        return redirect('cases:case_detail', pk=case.pk)

    # Vérifier qu'il y a des pannes sélectionnées
    if case.faults.count() == 0:
        messages.error(request, "Le dossier doit avoir au moins une panne sélectionnée pour créer un devis.")
        return redirect('cases:case_detail', pk=case.pk)

    if request.method == 'POST':
        form = QuoteCreateForm(request.POST)
        if form.is_valid():
            quote = form.save()

            # Créer automatiquement les lignes depuis les pannes sélectionnées
            settings = SystemSettings.get_settings()
            hourly_rate = settings.hourly_rate

            for fault in case.faults.all():
                # Ligne pour la main d'œuvre
                QuoteLine.objects.create(
                    quote=quote,
                    line_type='LABOR',
                    description=f"{fault.group.name} - {fault.name}: {fault.description}",
                    hours=fault.labor_hours,
                    hourly_rate=hourly_rate,
                    quantity=1
                )

                # Ligne pour les pièces si nécessaire
                if fault.parts_cost > 0:
                    QuoteLine.objects.create(
                        quote=quote,
                        line_type='PARTS',
                        description=f"Pièces pour {fault.name}",
                        quantity=1,
                        unit_price_ht=fault.parts_cost
                    )

            # Recalculer les totaux
            quote.calculate_totals()

            messages.success(request, f'Le devis a été créé avec succès. Vérifiez les lignes avant de l\'émettre.')
            return redirect('quotes:quote_edit_lines', pk=quote.pk)
    else:
        # Pré-remplir avec le dossier
        form = QuoteCreateForm(initial={'case': case})

    context = {
        'form': form,
        'case': case,
    }

    return render(request, 'quotes/quote_create.html', context)


@login_required
def quote_edit_lines(request, pk):
    """Modifier les lignes d'un devis (gestionnaire uniquement)"""
    if request.user.profile.role not in ['GESTIONNAIRE', 'ADMIN']:
        messages.error(request, "Vous n'avez pas les permissions pour modifier un devis.")
        return redirect('quotes:quote_list')

    quote = get_object_or_404(Quote, pk=pk)

    # Vérifier que le devis n'est pas encore validé
    if quote.is_validated_by_manager:
        messages.error(request, "Ce devis a déjà été validé et ne peut plus être modifié.")
        return redirect('quotes:quote_detail', pk=quote.pk)

    # Créer le formset pour les lignes
    QuoteLineFormSet = inlineformset_factory(
        Quote,
        QuoteLine,
        form=QuoteLineForm,
        extra=2,
        can_delete=True,
        min_num=1,
        validate_min=True
    )

    if request.method == 'POST':
        formset = QuoteLineFormSet(request.POST, instance=quote)
        if formset.is_valid():
            formset.save()

            # Recalculer les totaux
            quote.calculate_totals()

            messages.success(request, 'Les lignes du devis ont été mises à jour.')
            return redirect('quotes:quote_detail', pk=quote.pk)
    else:
        formset = QuoteLineFormSet(instance=quote)

    context = {
        'quote': quote,
        'formset': formset,
    }

    return render(request, 'quotes/quote_edit_lines.html', context)


@login_required
@transaction.atomic
def quote_validate(request, pk):
    """Valider et émettre un devis au client (gestionnaire uniquement)"""
    if request.user.profile.role not in ['GESTIONNAIRE', 'ADMIN']:
        messages.error(request, "Vous n'avez pas les permissions pour valider un devis.")
        return redirect('quotes:quote_list')

    quote = get_object_or_404(Quote, pk=pk)

    if quote.is_validated_by_manager:
        messages.error(request, "Ce devis a déjà été validé.")
        return redirect('quotes:quote_detail', pk=quote.pk)

    # Vérifier qu'il y a au moins une ligne
    if quote.lines.count() == 0:
        messages.error(request, "Le devis doit contenir au moins une ligne avant d'être validé.")
        return redirect('quotes:quote_edit_lines', pk=quote.pk)

    # Récupérer les lignes pour l'affichage
    quote_lines = quote.lines.all()

    if request.method == 'POST':
        form = QuoteValidateForm(request.POST)
        if form.is_valid():
            quote.is_validated_by_manager = True
            quote.save()

            # Mettre à jour le statut du dossier
            quote.case.status = 'DEVIS_EMIS'
            quote.case.save()

            # Create notification for client
            Notification.create_for_case_status_change(quote.case, quote.case.status)

            # Envoyer un email au client
            try:
                from garage.utils.email import send_quote_emitted_email
                send_quote_emitted_email(quote)
            except Exception as e:
                # Log l'erreur mais ne bloque pas le processus
                print(f"Erreur lors de l'envoi de l'email: {e}")

            messages.success(request, f'Le devis {quote.quote_number} a été validé et émis au client.')
            return redirect('quotes:quote_detail', pk=quote.pk)
    else:
        form = QuoteValidateForm()

    context = {
        'quote': quote,
        'quote_lines': quote_lines,
        'form': form,
        'now': timezone.now(),
    }

    return render(request, 'quotes/quote_validate.html', context)


@login_required
@transaction.atomic
def quote_accept(request, pk):
    """Accepter un devis (client uniquement)"""
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent accepter un devis.")
        return redirect('quotes:quote_list')

    quote = get_object_or_404(Quote, pk=pk, case__client=request.user)

    # Vérifier que le devis peut être accepté
    if not quote.is_validated_by_manager:
        messages.error(request, "Ce devis n'a pas encore été émis.")
        return redirect('quotes:quote_detail', pk=quote.pk)

    if quote.is_accepted_by_client:
        messages.info(request, "Ce devis a déjà été accepté.")
        return redirect('quotes:quote_detail', pk=quote.pk)

    if quote.is_refused_by_client:
        messages.error(request, "Ce devis a été refusé et ne peut plus être accepté.")
        return redirect('quotes:quote_detail', pk=quote.pk)

    if quote.is_expired():
        messages.error(request, "Ce devis a expiré et ne peut plus être accepté.")
        return redirect('quotes:quote_detail', pk=quote.pk)

    # Récupérer les lignes pour l'affichage
    quote_lines = quote.lines.all()

    if request.method == 'POST':
        form = QuoteAcceptForm(request.POST)
        if form.is_valid():
            quote.is_accepted_by_client = True
            quote.acceptance_date = timezone.now()
            quote.save()

            # Mettre à jour le statut du dossier
            case = quote.case
            case.status = 'DEVIS_ACCEPTE'
            case.save()

            # Create notification for client
            Notification.create_for_case_status_change(case, case.status)

            # Notifier les gestionnaires de l'acceptation du devis
            Notification.notify_managers_quote_accepted(case)

            # Envoyer un email aux gestionnaires
            try:
                from garage.utils.email import send_quote_accepted_email
                send_quote_accepted_email(quote)
            except Exception as e:
                # Log l'erreur mais ne bloque pas le processus
                print(f"Erreur lors de l'envoi de l'email: {e}")

            messages.success(request, f'Le devis {quote.quote_number} a été accepté. Vous pouvez maintenant réserver un rendez-vous.')
            return redirect('cases:case_detail', pk=case.pk)
    else:
        form = QuoteAcceptForm()

    context = {
        'quote': quote,
        'quote_lines': quote_lines,
        'form': form,
    }

    return render(request, 'quotes/quote_accept.html', context)


@login_required
@transaction.atomic
def quote_refuse(request, pk):
    """Refuser un devis (client uniquement)"""
    if request.user.profile.role != 'CLIENT':
        messages.error(request, "Seuls les clients peuvent refuser un devis.")
        return redirect('quotes:quote_list')

    quote = get_object_or_404(Quote, pk=pk, case__client=request.user)

    # Vérifier que le devis peut être refusé
    if not quote.is_validated_by_manager:
        messages.error(request, "Ce devis n'a pas encore été émis.")
        return redirect('quotes:quote_detail', pk=quote.pk)

    if quote.is_accepted_by_client:
        messages.error(request, "Ce devis a déjà été accepté et ne peut plus être refusé.")
        return redirect('quotes:quote_detail', pk=quote.pk)

    if quote.is_refused_by_client:
        messages.info(request, "Ce devis a déjà été refusé.")
        return redirect('quotes:quote_detail', pk=quote.pk)

    if request.method == 'POST':
        form = QuoteRefuseForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data.get('reason', '')
            quote.is_refused_by_client = True
            quote.refusal_reason = reason
            quote.save()

            # Mettre à jour le statut du dossier
            case = quote.case
            case.status = 'DEVIS_REFUSE'
            case.save()

            # Envoyer un email aux gestionnaires
            try:
                from garage.utils.email import send_quote_refused_email
                send_quote_refused_email(quote)
            except Exception as e:
                # Log l'erreur mais ne bloque pas le processus
                print(f"Erreur lors de l'envoi de l'email: {e}")

            messages.success(request, f'Le devis {quote.quote_number} a été refusé.')
            return redirect('cases:case_detail', pk=case.pk)
    else:
        form = QuoteRefuseForm()

    context = {
        'quote': quote,
        'form': form,
    }

    return render(request, 'quotes/quote_refuse.html', context)


@login_required
def quote_download_pdf(request, pk):
    """Télécharger un devis en PDF"""
    from django.http import HttpResponse
    from garage.utils.pdf import generate_quote_pdf

    # Vérifier les permissions
    if request.user.profile.role == 'CLIENT':
        quote = get_object_or_404(Quote, pk=pk, case__client=request.user)
    else:
        quote = get_object_or_404(Quote, pk=pk)

    # Vérifier que le devis est validé
    if not quote.is_validated_by_manager:
        messages.error(request, "Seuls les devis validés peuvent être téléchargés en PDF.")
        return redirect('quotes:quote_detail', pk=quote.pk)

    # Générer le PDF
    try:
        pdf_file = generate_quote_pdf(quote)

        # Créer la réponse HTTP
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="devis_{quote.quote_number}.pdf"'

        return response
    except RuntimeError as e:
        messages.error(request, f"Impossible de générer le PDF: {str(e)}")
        return redirect('quotes:quote_detail', pk=quote.pk)
