# garage/billing/admin.py

from django.contrib import admin
from .models import Invoice, InvoiceLine, Payment


class InvoiceLineInline(admin.TabularInline):
    """Inline pour afficher les lignes de facture"""
    model = InvoiceLine
    extra = 0
    fields = ('description', 'quantity', 'unit_price_ht', 'total_ht')
    readonly_fields = ('total_ht',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin pour gérer les factures"""
    list_display = ('invoice_number', 'case', 'total_ttc', 'is_paid', 'payment_date', 'created_at')
    list_filter = ('is_paid', 'created_at', 'payment_date')
    search_fields = ('invoice_number', 'case__id', 'case__client__username')
    readonly_fields = ('invoice_number', 'created_at', 'updated_at', 'total_ht', 'total_vat', 'total_ttc')
    inlines = [InvoiceLineInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Dossier', {
            'fields': ('case', 'related_quote', 'invoice_number')
        }),
        ('Montants', {
            'fields': ('total_ht', 'vat_rate', 'total_vat', 'total_ttc'),
            'description': 'Calculés automatiquement depuis le devis'
        }),
        ('Paiement', {
            'fields': ('is_paid', 'payment_date')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    """Admin pour gérer les lignes de facture"""
    list_display = ('invoice', 'description', 'quantity', 'unit_price_ht', 'total_ht')
    list_filter = ('invoice__created_at',)
    search_fields = ('description', 'invoice__invoice_number')
    readonly_fields = ('total_ht',)

    fieldsets = (
        ('Facture', {
            'fields': ('invoice',)
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Montants', {
            'fields': ('quantity', 'unit_price_ht', 'total_ht')
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin pour gérer les paiements"""
    list_display = ('invoice', 'amount', 'payment_method', 'status', 'transaction_id', 'created_at', 'completed_at')
    list_filter = ('status', 'payment_method', 'created_at', 'completed_at')
    search_fields = ('invoice__invoice_number', 'transaction_id')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Facture', {
            'fields': ('invoice',)
        }),
        ('Paiement', {
            'fields': ('amount', 'payment_method', 'status')
        }),
        ('Transaction', {
            'fields': ('transaction_id',),
            'description': 'Référence externe (Stripe, PayPal, etc.)'
        }),
        ('Dates', {
            'fields': ('created_at', 'completed_at')
        }),
    )
