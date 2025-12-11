# garage/quotes/admin.py

from django.contrib import admin
from .models import Quote, QuoteLine


class QuoteLineInline(admin.TabularInline):
    """Inline pour afficher les lignes de devis"""
    model = QuoteLine
    extra = 1
    fields = ('line_type', 'description', 'hours', 'hourly_rate', 'quantity', 'unit_price_ht', 'total_ht')
    readonly_fields = ('total_ht',)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    """Admin pour gérer les devis"""
    list_display = ('quote_number', 'case', 'total_ttc', 'validity_date', 'is_validated_by_manager',
                    'is_accepted_by_client', 'is_expired_display', 'created_at')
    list_filter = ('is_validated_by_manager', 'is_accepted_by_client', 'is_refused_by_client',
                   'created_at', 'validity_date')
    search_fields = ('quote_number', 'case__id', 'case__client__username')
    readonly_fields = ('quote_number', 'created_at', 'updated_at', 'total_labor', 'total_parts',
                      'total_ht', 'total_vat', 'total_ttc', 'is_expired_display')
    inlines = [QuoteLineInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Dossier', {
            'fields': ('case', 'quote_number')
        }),
        ('Montants', {
            'fields': ('total_labor', 'total_parts', 'total_ht', 'vat_rate', 'total_vat', 'total_ttc'),
            'description': 'Calculés automatiquement à partir des lignes'
        }),
        ('Validité', {
            'fields': ('created_at', 'validity_date', 'is_expired_display')
        }),
        ('États', {
            'fields': ('is_validated_by_manager', 'is_accepted_by_client', 'is_refused_by_client',
                      'refusal_reason', 'acceptance_date')
        }),
        ('Métadonnées', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def is_expired_display(self, obj):
        """Affiche si le devis est expiré"""
        return "Oui" if obj.is_expired() else "Non"
    is_expired_display.short_description = 'Expiré'
    is_expired_display.boolean = True

    actions = ['recalculate_totals', 'validate_quotes']

    def recalculate_totals(self, request, queryset):
        """Action pour recalculer les totaux"""
        for quote in queryset:
            quote.calculate_totals()
        self.message_user(request, f"{queryset.count()} devis recalculés.")
    recalculate_totals.short_description = "Recalculer les totaux"

    def validate_quotes(self, request, queryset):
        """Action pour valider plusieurs devis"""
        queryset.filter(is_validated_by_manager=False).update(is_validated_by_manager=True)
        self.message_user(request, f"{queryset.count()} devis validés.")
    validate_quotes.short_description = "Valider les devis sélectionnés"


@admin.register(QuoteLine)
class QuoteLineAdmin(admin.ModelAdmin):
    """Admin pour gérer les lignes de devis"""
    list_display = ('quote', 'line_type', 'description', 'hours', 'quantity', 'total_ht')
    list_filter = ('line_type', 'quote__created_at')
    search_fields = ('description', 'quote__quote_number')
    readonly_fields = ('total_ht',)

    fieldsets = (
        ('Devis', {
            'fields': ('quote', 'line_type')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Main d\'Œuvre', {
            'fields': ('hours', 'hourly_rate'),
            'description': 'Pour les lignes de type "Main d\'œuvre"'
        }),
        ('Pièces', {
            'fields': ('quantity', 'unit_price_ht'),
            'description': 'Pour les lignes de type "Pièces"'
        }),
        ('Total', {
            'fields': ('total_ht',)
        }),
    )
