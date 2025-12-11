# garage/vehicles/admin.py

from django.contrib import admin
from .models import Vehicle, VehicleHistory


class VehicleHistoryInline(admin.TabularInline):
    """Inline pour afficher l'historique avec le véhicule"""
    model = VehicleHistory
    extra = 0
    readonly_fields = ('event_date', 'event_type', 'description')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """Empêche l'ajout manuel d'historique via l'inline"""
        return False


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Admin pour gérer les véhicules"""
    list_display = ('get_identifier', 'brand', 'model', 'year', 'owner', 'mileage', 'is_active', 'created_at')
    list_filter = ('is_active', 'brand', 'year', 'fuel_type', 'created_at')
    search_fields = ('plate_number', 'nickname', 'brand', 'model', 'owner__username', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [VehicleHistoryInline]

    fieldsets = (
        ('Propriétaire', {
            'fields': ('owner',)
        }),
        ('Informations Principales', {
            'fields': ('brand', 'model', 'year', 'mileage', 'fuel_type')
        }),
        ('Identification', {
            'fields': ('plate_number', 'nickname'),
            'description': 'Au moins l\'immatriculation OU le surnom est obligatoire'
        }),
        ('Contrôles et Assurance', {
            'fields': ('last_technical_inspection', 'insurance_company', 'insurance_expiry_date')
        }),
        ('Notes', {
            'fields': ('notes',),
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

    def get_identifier(self, obj):
        """Retourne l'identifiant du véhicule"""
        return obj.get_identifier()
    get_identifier.short_description = 'Identifiant'


@admin.register(VehicleHistory)
class VehicleHistoryAdmin(admin.ModelAdmin):
    """Admin pour consulter l'historique des véhicules"""
    list_display = ('vehicle', 'event_type', 'event_date', 'description_short')
    list_filter = ('event_type', 'event_date')
    search_fields = ('vehicle__plate_number', 'vehicle__nickname', 'description')
    readonly_fields = ('vehicle', 'event_date', 'event_type', 'description')
    date_hierarchy = 'event_date'

    def description_short(self, obj):
        """Affiche une version courte de la description"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

    def has_add_permission(self, request):
        """Empêche l'ajout manuel via l'admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression"""
        return False
