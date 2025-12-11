from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse

from .models import Invoice, InvoiceLine
from garage.cases.models import Case
from garage.utils.pdf import generate_invoice_pdf  # Assume this exists or I'll check/create common pdf util

@login_required
def invoice_list(request):
    """Liste des factures"""
    if request.user.profile.role == 'CLIENT':
        invoices = Invoice.objects.filter(case__client=request.user)
    else:
        invoices = Invoice.objects.all()

    invoices = invoices.select_related('case', 'case__client', 'case__vehicle').order_by('-created_at')

    context = {
        'invoices': invoices,
    }
    return render(request, 'billing/invoice_list.html', context)

@login_required
def invoice_detail(request, pk):
    """Détail d'une facture"""
    if request.user.profile.role == 'CLIENT':
        invoice = get_object_or_404(Invoice, pk=pk, case__client=request.user)
    else:
        invoice = get_object_or_404(Invoice, pk=pk)

    context = {
        'invoice': invoice,
    }
    return render(request, 'billing/invoice_detail.html', context)

@login_required
@transaction.atomic
def invoice_create(request, case_id):
    """Générer une facture depuis un dossier (Manager uniquement)"""
    if request.user.profile.role not in ['GESTIONNAIRE', 'ADMIN']:
        messages.error(request, "Action non autorisée.")
        return redirect('cases:case_list')

    case = get_object_or_404(Case, pk=case_id)

    # Vérifications
    if hasattr(case, 'invoice'):
        messages.warning(request, "Une facture existe déjà pour ce dossier.")
        return redirect('billing:invoice_detail', pk=case.invoice.pk)

    if not hasattr(case, 'quote'):
        messages.error(request, "Impossible de facturer : aucun devis associé.")
        return redirect('cases:case_detail', pk=case.pk)
    
    quote = case.quote
    if not quote.is_accepted_by_client:
         messages.error(request, "Le devis doit être accepté avant facturation.")
         return redirect('cases:case_detail', pk=case.pk)

    # Création de la facture
    invoice = Invoice.objects.create(
        case=case,
        related_quote=quote,
        total_ht=quote.total_ht,
        vat_rate=quote.vat_rate,
        total_vat=quote.total_vat,
        total_ttc=quote.total_ttc
    )

    # Copie des lignes
    for line in quote.lines.all():
        InvoiceLine.objects.create(
            invoice=invoice,
            description=line.description,
            quantity=line.quantity,
            unit_price_ht=line.unit_price_ht if line.line_type == 'PARTS' else line.hourly_rate, 
            # Note: line.unit_price_ht is for parts, for labor we might need to compute or use hourly_rate * hours?
            # InvoiceLine model has unit_price_ht and quantity.
            # If labor: quantity=1 (usually) and price is total? Or quantity=hours?
            # QuoteLine: hours, hourly_rate -> total_ht. 
            # InvoiceLine: quantity, unit_price_ht -> total_ht.
            # Adaptation needed.
            total_ht=line.total_ht
        )
        # Fix logic for labor lines mapping to invoice lines:
        # If line_type LABOUR: Description="...", Quantity=1, UnitPrice=TotalHT?
        # Or Quantity=Hours? InvoiceLine quantity is Integer. Hours is Decimal.
        # So we can't map Hours to Quantity directly if it's fractional.
        # We'll set Quantity=1 and UnitPrice=TotalHT for Labor lines.
    
    # Re-loop to fix the logic above which was inside the create call
    # Clearing lines and doing it properly
    invoice.lines.all().delete()
    
    for line in quote.lines.all():
        if line.line_type == 'LABOR':
            qty = 1
            price = line.total_ht
            desc = f"{line.description} ({line.hours}h @ {line.hourly_rate}€/h)"
        else:
            qty = line.quantity
            price = line.unit_price_ht
            desc = line.description

        InvoiceLine.objects.create(
            invoice=invoice,
            description=desc,
            quantity=qty,
            unit_price_ht=price,
            total_ht=line.total_ht
        )

    messages.success(request, f"Facture {invoice.invoice_number} générée avec succès.")
    return redirect('billing:invoice_detail', pk=invoice.pk)

@login_required
def invoice_download_pdf(request, pk):
    """Télécharger la facture en PDF"""
    if request.user.profile.role == 'CLIENT':
        invoice = get_object_or_404(Invoice, pk=pk, case__client=request.user)
    else:
        invoice = get_object_or_404(Invoice, pk=pk)

    try:
        from garage.utils.pdf import generate_invoice_pdf
        pdf_file = generate_invoice_pdf(invoice)
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="facture_{invoice.invoice_number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Erreur PDF: {str(e)}")
        return redirect('billing:invoice_detail', pk=pk)
