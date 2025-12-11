# garage/catalog/admin.py

from django.contrib import admin
from .models import FaultGroup, Fault, SystemSettings


class FaultInline(admin.TabularInline):
    """Inline pour afficher les pannes dans un groupe"""
    model = Fault
    extra = 1
    fields = ('name', 'labor_hours', 'parts_name', 'parts_cost', 'is_active')
    show_change_link = True


@admin.register(FaultGroup)
class FaultGroupAdmin(admin.ModelAdmin):
    """Admin pour gérer les groupes de pannes"""
    list_display = ('name', 'order', 'icon', 'fault_count', 'created_at')
    list_editable = ('order',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [FaultInline]

    fieldsets = (
        ('Informations', {
            'fields': ('name', 'description', 'icon', 'order')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def fault_count(self, obj):
        """Compte le nombre de pannes dans le groupe"""
        return obj.faults.count()
    fault_count.short_description = 'Nombre de pannes'


@admin.register(Fault)
class FaultAdmin(admin.ModelAdmin):
    """Admin pour gérer les pannes"""
    list_display = ('name', 'group', 'labor_hours', 'parts_name', 'parts_cost', 'total_ht', 'is_active')
    list_filter = ('group', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'parts_name')
    readonly_fields = ('created_at', 'updated_at', 'total_ht_display')
    list_editable = ('is_active',)

    fieldsets = (
        ('Groupe', {
            'fields': ('group',)
        }),
        ('Informations', {
            'fields': ('name', 'description')
        }),
        ('Barème Main d\'Œuvre', {
            'fields': ('labor_hours',),
            'description': 'Temps en heures (ex: 1.5 pour 1h30)'
        }),
        ('Pièces', {
            'fields': ('parts_name', 'parts_cost'),
            'description': 'Coût des pièces en euros'
        }),
        ('Calcul', {
            'fields': ('total_ht_display',),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_ht(self, obj):
        """Calcule et affiche le total HT"""
        return f"{obj.calculate_total_ht():.2f} €"
    total_ht.short_description = 'Total HT'

    def total_ht_display(self, obj):
        """Affiche le calcul détaillé du total HT"""
        labor_cost = obj.calculate_labor_cost()
        return f"MO: {labor_cost:.2f}€ + Pièces: {obj.parts_cost:.2f}€ = {obj.calculate_total_ht():.2f}€ HT"
    total_ht_display.short_description = 'Calcul Total HT'


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin pour gérer les paramètres système (Singleton)"""
    list_display = ('hourly_rate', 'vat_rate_percent', 'quote_validity_days', 'appointment_cancel_hours')
    readonly_fields = ('updated_at',)

    fieldsets = (
        ('Tarification', {
            'fields': ('hourly_rate', 'vat_rate'),
            'description': 'Paramètres de base pour le calcul des devis'
        }),
        ('Devis', {
            'fields': ('quote_validity_days', 'quote_variation_threshold'),
            'description': 'Gestion des devis'
        }),
        ('Rendez-vous', {
            'fields': ('appointment_cancel_hours',),
            'description': 'Délai minimum pour annuler/modifier un RDV'
        }),
        ('Métadonnées', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def vat_rate_percent(self, obj):
        """Affiche le taux TVA en pourcentage"""
        return f"{obj.vat_rate * 100:.0f}%"
    vat_rate_percent.short_description = 'TVA'

    def has_add_permission(self, request):
        """Empêche la création de multiples instances (Singleton)"""
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression"""
        return False
