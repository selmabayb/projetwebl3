# garage/notifications/admin.py

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin pour gérer les notifications"""
    list_display = ('status_icon', 'user', 'title', 'notification_type', 'related_case', 'is_read', 'created_at')
    list_filter = ('is_read', 'notification_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']

    fieldsets = (
        ('Destinataire', {
            'fields': ('user',)
        }),
        ('Contenu', {
            'fields': ('title', 'message', 'notification_type')
        }),
        ('Lien', {
            'fields': ('related_case',),
            'description': 'Dossier concerné par la notification'
        }),
        ('Statut', {
            'fields': ('is_read', 'read_at')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def status_icon(self, obj):
        """Affiche une icône selon le statut lu/non lu"""
        return "✓" if obj.is_read else "●"
    status_icon.short_description = ''

    def mark_as_read(self, request, queryset):
        """Action pour marquer comme lu"""
        from django.utils import timezone
        count = queryset.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        self.message_user(request, f"{count} notification(s) marquée(s) comme lue(s).")
    mark_as_read.short_description = "Marquer comme lue"

    def mark_as_unread(self, request, queryset):
        """Action pour marquer comme non lu"""
        count = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f"{count} notification(s) marquée(s) comme non lue(s).")
    mark_as_unread.short_description = "Marquer comme non lue"
