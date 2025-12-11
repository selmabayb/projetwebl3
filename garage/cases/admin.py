# garage/cases/admin.py

from django.contrib import admin
from .models import Case, StatusLog


class StatusLogInline(admin.TabularInline):
    """Inline pour afficher l'historique des statuts"""
    model = StatusLog
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'changed_at', 'comment')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """Empêche l'ajout manuel via l'inline"""
        return False


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    """Admin pour gérer les dossiers"""
    list_display = ('id', 'client', 'vehicle', 'status', 'estimated_completion', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('client__username', 'client__email', 'vehicle__plate_number', 'vehicle__nickname')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('faults',)
    inlines = [StatusLogInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Client et Véhicule', {
            'fields': ('client', 'vehicle')
        }),
        ('Pannes Sélectionnées', {
            'fields': ('faults',),
            'description': 'Pannes déclarées par le client'
        }),
        ('Statut', {
            'fields': ('status', 'estimated_completion')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Override pour créer un log de statut si le statut change"""
        if change and 'status' in form.changed_data:
            old_status = Case.objects.get(pk=obj.pk).status
            super().save_model(request, obj, form, change)
            StatusLog.objects.create(
                case=obj,
                old_status=old_status,
                new_status=obj.status,
                changed_by=request.user,
                comment=f"Changement via admin Django"
            )
        else:
            super().save_model(request, obj, form, change)


@admin.register(StatusLog)
class StatusLogAdmin(admin.ModelAdmin):
    """Admin pour consulter l'historique des statuts"""
    list_display = ('case', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status', 'changed_at')
    search_fields = ('case__id', 'case__client__username', 'comment')
    readonly_fields = ('case', 'old_status', 'new_status', 'changed_by', 'changed_at', 'comment')
    date_hierarchy = 'changed_at'

    def has_add_permission(self, request):
        """Empêche l'ajout manuel"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression"""
        return False
