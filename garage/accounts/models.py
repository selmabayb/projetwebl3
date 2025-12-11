# garage/accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extension du modèle User Django pour stocker les informations supplémentaires.
    BF1-4: Gestion des comptes utilisateurs avec rôles
    """
    ROLE_CHOICES = [
        ('CLIENT', 'Client'),
        ('GESTIONNAIRE', 'Gestionnaire'),  # Technicien/Manager
        ('ADMIN', 'Administrateur'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CLIENT', verbose_name="Rôle")

    # Informations complémentaires (BF39, BF6)
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")

    # Sécurité (BNF13): verrouillage compte après échecs
    failed_login_attempts = models.IntegerField(default=0, verbose_name="Tentatives de connexion échouées")
    account_locked_until = models.DateTimeField(blank=True, null=True, verbose_name="Compte verrouillé jusqu'à")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    def is_client(self):
        """Vérifie si l'utilisateur est un client"""
        return self.role == 'CLIENT'

    def is_gestionnaire(self):
        """Vérifie si l'utilisateur est un gestionnaire"""
        return self.role == 'GESTIONNAIRE'

    def is_admin(self):
        """Vérifie si l'utilisateur est un administrateur"""
        return self.role == 'ADMIN'


# Signal pour créer et sauvegarder automatiquement un profil
@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """
    Crée automatiquement un UserProfile lors de la création d'un User
    et le sauvegarde lors des mises à jour
    """
    if created:
        UserProfile.objects.create(user=instance)
    elif hasattr(instance, 'profile'):
        instance.profile.save()
