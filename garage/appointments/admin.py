# garage/appointments/admin.py

from django.contrib import admin
from .models import Appointment, AppointmentSlot


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    """Admin pour gérer les créneaux de rendez-vous"""
    list_display = ('display_name', 'is_recurring', 'weekday_display', 'date', 'start_time', 'end_time', 'is_available', 'is_exception')
    list_filter = ('is_recurring', 'is_available', 'is_exception', 'weekday', 'created_at')
    list_editable = ('is_available',)
    search_fields = ('date',)

    fieldsets = (
        ('Type de Créneau', {
            'fields': ('is_recurring', 'is_exception'),
            'description': 'Récurrent = chaque semaine, Exception = jour férié/fermeture'
        }),
        ('Planification', {
            'fields': ('weekday', 'date'),
            'description': 'Weekday pour récurrent, Date pour ponctuel/exception'
        }),
        ('Horaire', {
            'fields': ('start_time', 'end_time')
        }),
        ('Disponibilité', {
            'fields': ('is_available',)
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def display_name(self, obj):
        """Affiche le nom du créneau"""
        return str(obj)
    display_name.short_description = 'Créneau'

    def weekday_display(self, obj):
        """Affiche le jour de la semaine"""
        return obj.get_weekday_display() if obj.weekday is not None else '-'
    weekday_display.short_description = 'Jour'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin pour gérer les rendez-vous"""
    list_display = ('case', 'client_name', 'vehicle', 'date', 'start_time', 'end_time', 'is_cancelled', 'created_at')
    list_filter = ('is_cancelled', 'date', 'created_at')
    search_fields = ('case__client__username', 'case__client__email', 'case__vehicle__plate_number')
    readonly_fields = ('created_at', 'updated_at', 'cancellation_date', 'can_modify', 'can_cancel')
    date_hierarchy = 'date'

    fieldsets = (
        ('Dossier', {
            'fields': ('case',)
        }),
        ('Rendez-vous', {
            'fields': ('date', 'start_time', 'end_time')
        }),
        ('Annulation', {
            'fields': ('is_cancelled', 'cancellation_date', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('can_modify', 'can_cancel'),
            'classes': ('collapse',),
            'description': 'Indique si le RDV peut être modifié/annulé (>24h avant)'
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def client_name(self, obj):
        """Affiche le nom du client"""
        return obj.case.client.get_full_name() or obj.case.client.username
    client_name.short_description = 'Client'

    def vehicle(self, obj):
        """Affiche le véhicule"""
        return str(obj.case.vehicle)
    vehicle.short_description = 'Véhicule'

    def can_modify(self, obj):
        """Indique si le RDV peut être modifié"""
        return "Oui" if obj.can_be_modified() else "Non (< 24h)"
    can_modify.short_description = 'Peut modifier'

    def can_cancel(self, obj):
        """Indique si le RDV peut être annulé"""
        return "Oui" if obj.can_be_cancelled() else "Non (< 24h)"
    can_cancel.short_description = 'Peut annuler'
