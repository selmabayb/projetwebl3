# garage/catalog/models.py

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class FaultGroup(models.Model):
    """
    Groupe de pannes (Carrosserie, Pneus, Pare-brise, Moteur, etc.)
    BF40: Configuration des groupes de pannes
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du groupe")
    description = models.TextField(blank=True, verbose_name="Description")
    icon = models.CharField(max_length=50, blank=True, help_text="Icône CSS (ex: fa-car)", verbose_name="Icône")
    order = models.IntegerField(default=0, help_text="Ordre d'affichage", verbose_name="Ordre")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        verbose_name = "Groupe de Pannes"
        verbose_name_plural = "Groupes de Pannes"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Fault(models.Model):
    """
    Sous-panne appartenant à un groupe avec barème (heures MO + prix pièces)
    BF41: Définir les barèmes pour chaque sous-panne
    Tableau 8: Barèmes complets des pannes configurées
    """
    group = models.ForeignKey(FaultGroup, on_delete=models.CASCADE, related_name='faults', verbose_name="Groupe")
    name = models.CharField(max_length=200, verbose_name="Nom de la panne")
    description = models.TextField(blank=True, verbose_name="Description détaillée")

    # Barème main d'œuvre
    labor_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Temps de main d'œuvre en heures (ex: 1.5)",
        verbose_name="Heures de MO"
    )

    # Coût des pièces
    parts_name = models.CharField(max_length=200, blank=True, verbose_name="Nom de la pièce")
    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Coût des pièces en euros",
        verbose_name="Coût pièces (€)"
    )

    # Actif/Inactif
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        verbose_name = "Panne (Sous-catégorie)"
        verbose_name_plural = "Pannes (Sous-catégories)"
        ordering = ['group__order', 'group__name', 'name']
        unique_together = ['group', 'name']

    def __str__(self):
        return f"{self.group.name} - {self.name}"

    def calculate_labor_cost(self, hourly_rate=None):
        """
        Calcule le coût de la main d'œuvre
        Formula: heures × taux_horaire (Section 6.4)
        """
        if hourly_rate is None:
            # Use import inside method to avoid circular import if any (though SystemSettings is in same file)
            # SystemSettings is defined below? No, later in file.
            # But they are in the same module.
            # Wait, SystemSettings is defined AFTER Fault. This is a problem for type hinting/usage if referencing class directly? 
            # No, Python resolves at runtime.
            # But SystemSettings class is defined AFTER Fault class in the file.
            # So I should use `SystemSettings` inside the method, it will be available at runtime.
            
            # However, I should probably move SystemSettings definition BEFORE Fault or use string/lazy?
            # Or just assume it works at runtime (it does).
            try:
                # We need to access SystemSettings class. It's defined later in the file.
                # In Python methods, global lookup happens at call time. So if SystemSettings is defined in the module, it's fine.
                settings = SystemSettings.get_settings()
                hourly_rate = settings.hourly_rate
            except NameError:
                 # Fallback if SystemSettings not defined yet? Unlikely in run time.
                 hourly_rate = Decimal('60.00')

        return self.labor_hours * Decimal(str(hourly_rate))

    def calculate_total_ht(self, hourly_rate=None):
        """
        Calcule le total HT (MO + pièces)
        """
        return self.calculate_labor_cost(hourly_rate) + self.parts_cost


class SystemSettings(models.Model):
    """
    Paramètres globaux du système (taux horaire, TVA, etc.)
    BF42: Paramétrer le taux horaire et la TVA
    Singleton pattern: une seule instance en base
    """
    # Tarification
    hourly_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('60.00'),
        validators=[MinValueValidator(Decimal('1.00'))],
        help_text="Taux horaire de main d'œuvre en euros",
        verbose_name="Taux horaire (€/h)"
    )

    vat_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.20'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Taux de TVA (ex: 0.20 pour 20%)",
        verbose_name="Taux de TVA"
    )

    # Validité des devis
    quote_validity_days = models.IntegerField(
        default=15,
        validators=[MinValueValidator(1)],
        help_text="Nombre de jours de validité d'un devis",
        verbose_name="Validité devis (jours)"
    )

    # Paramètres RDV
    appointment_cancel_hours = models.IntegerField(
        default=24,
        validators=[MinValueValidator(1)],
        help_text="Délai minimum (en heures) pour annuler/modifier un RDV",
        verbose_name="Délai annulation RDV (h)"
    )

    # Seuil notification variation devis (BF49)
    quote_variation_threshold = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.10'),
        help_text="Seuil de variation pour notification (ex: 0.10 pour 10%)",
        verbose_name="Seuil variation devis"
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        verbose_name = "Paramètres Système"
        verbose_name_plural = "Paramètres Système"

    def __str__(self):
        return f"Paramètres Système (Taux: {self.hourly_rate}€/h, TVA: {self.vat_rate*100}%)"

    def save(self, *args, **kwargs):
        """Override save pour assurer qu'il n'y a qu'une seule instance (Singleton)"""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Récupère ou crée l'instance unique des paramètres"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
