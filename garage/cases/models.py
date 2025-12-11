# garage/cases/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Case(models.Model):
    """
    Dossier de réparation client
    BF22-25: Gestion des dossiers
    Workflow: NOUVEAU → DEVIS_ÉMIS → DEVIS_ACCEPTÉ → RDV_CONFIRMÉ → EN_COURS → PRÊT → CLÔTURÉ
    """
    STATUS_CHOICES = [
        ('NOUVEAU', 'Nouveau'),
        ('DEVIS_EMIS', 'Devis émis'),
        ('DEVIS_ACCEPTE', 'Devis accepté'),
        ('DEVIS_REFUSE', 'Devis refusé'),
        ('RDV_CONFIRME', 'RDV confirmé'),
        ('EN_COURS', 'En cours'),
        ('PRET', 'Prêt'),
        ('CLOTURE', 'Clôturé'),
        ('EXPIRE', 'Expiré'),
    ]

    URGENCY_CHOICES = [
        ('BASSE', 'Basse'),
        ('NORMALE', 'Normale'),
        ('HAUTE', 'Haute'),
    ]

    # Relations
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cases', verbose_name="Client")
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='cases',
        verbose_name="Véhicule"
    )

    # Description du problème
    description = models.TextField(
        verbose_name="Description du problème",
        help_text="Description détaillée du problème rencontré"
    )

    # Niveau d'urgence
    urgency_level = models.CharField(
        max_length=10,
        choices=URGENCY_CHOICES,
        default='NORMALE',
        verbose_name="Niveau d'urgence"
    )

    # Pannes sélectionnées par le client (BF10)
    faults = models.ManyToManyField(
        'catalog.Fault',
        related_name='cases',
        verbose_name="Pannes sélectionnées",
        help_text="Pannes déclarées par le client",
        blank=True
    )

    # Statut et workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NOUVEAU',
        verbose_name="Statut"
    )

    # ETA (Estimation de fin de réparation) - BF30
    estimated_completion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Estimation de fin (ETA)",
        help_text="Date et heure estimée de fin de réparation"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        verbose_name = "Dossier"
        verbose_name_plural = "Dossiers"
        ordering = ['-created_at']

    def __str__(self):
        return f"Dossier #{self.id} - {self.client.get_full_name()} - {self.get_status_display()}"

    def can_accept_quote(self):
        """Vérifie si le client peut accepter le devis"""
        return self.status == 'DEVIS_EMIS'

    def can_book_appointment(self):
        """Vérifie si le client peut prendre RDV (BF16)"""
        return self.status == 'DEVIS_ACCEPTE'

    def can_modify_appointment(self):
        """Vérifie si le client peut modifier son RDV"""
        return self.status == 'RDV_CONFIRME' and self.appointment_set.exists()

    def can_cancel_appointment(self):
        """Vérifie si le client peut annuler son RDV"""
        return self.status == 'RDV_CONFIRME' and self.appointment_set.exists()

    def get_timeline(self):
        """Retourne la timeline des changements de statut (BF19)"""
        return self.status_logs.all().order_by('timestamp')


class StatusLog(models.Model):
    """
    Historique des changements de statut d'un dossier
    BF31: Historiser les changements de statut
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='status_logs', verbose_name="Dossier")
    old_status = models.CharField(max_length=20, blank=True, verbose_name="Ancien statut")
    new_status = models.CharField(max_length=20, verbose_name="Nouveau statut")
    comment = models.TextField(blank=True, verbose_name="Commentaire")
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Modifié par"
    )
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Date et heure")

    class Meta:
        verbose_name = "Log de Statut"
        verbose_name_plural = "Logs de Statuts"
        ordering = ['changed_at']

    def __str__(self):
        return f"{self.case} - {self.old_status} → {self.new_status} ({self.changed_at.strftime('%d/%m/%Y %H:%M')})"
