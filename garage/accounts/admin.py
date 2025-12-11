# garage/accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin pour afficher le profil avec l'utilisateur"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    """Admin personnalisé pour User avec profil intégré"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_role(self, obj):
        """Affiche le rôle de l'utilisateur"""
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else '-'
    get_role.short_description = 'Rôle'


# Désenregistrer le User par défaut et enregistrer notre version personnalisée
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin pour gérer directement les profils"""
    list_display = ('user', 'role', 'phone_number', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'role')
        }),
        ('Informations Complémentaires', {
            'fields': ('phone_number', 'address')
        }),
        ('Sécurité', {
            'fields': ('failed_login_attempts', 'account_locked_until'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
