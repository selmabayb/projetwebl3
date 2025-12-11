# garage/vehicles/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from datetime import datetime


class Vehicle(models.Model):
    """
    Véhicule client avec toutes les informations requises
    BF5-8: Gestion des véhicules (ajout, modification, suppression, consultation)
    Validations: Tableau 6 du cahier des charges
    """
    # Propriétaire
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles', verbose_name="Propriétaire")

    # Informations principales (BF5)
    brand = models.CharField(
        max_length=50,
        verbose_name="Marque",
        help_text="2-50 caractères"
    )
    model = models.CharField(
        max_length=50,
        verbose_name="Modèle",
        help_text="2-50 caractères"
    )
    year = models.IntegerField(
        validators=[
            MinValueValidator(1950, message="L'année doit être supérieure à 1950"),
            MaxValueValidator(datetime.now().year, message="L'année ne peut pas être dans le futur")
        ],
        verbose_name="Année",
        help_text="Entre 1950 et année courante"
    )

    # Identification (au moins un des deux requis)
    plate_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{2}-[0-9]{3}-[A-Z]{2}$',
                message="Format invalide. Utiliser: AA-123-AA",
                code='invalid_plate'
            )
        ],
        verbose_name="Immatriculation",
        help_text="Format: AA-123-AA (optionnel si surnom fourni)"
    )

    nickname = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Surnom du véhicule",
        help_text="Obligatoire si pas d'immatriculation, 2-30 caractères (ex: 'Voiture principale')"
    )

    # Informations techniques
    mileage = models.IntegerField(
        validators=[
            MinValueValidator(1, message="Le kilométrage doit être positif"),
            MaxValueValidator(999999, message="Le kilométrage maximum est 999 999 km")
        ],
        verbose_name="Kilométrage (km)",
        help_text="Entre 1 et 999 999"
    )

    # Choix de carburants
    FUEL_TYPE_CHOICES = [
        ('ESSENCE', 'Essence'),
        ('DIESEL', 'Diesel'),
        ('ELECTRIQUE', 'Électrique'),
        ('HYBRIDE', 'Hybride'),
        ('GPL', 'GPL'),
        ('AUTRE', 'Autre'),
    ]

    fuel_type = models.CharField(
        max_length=50,
        choices=FUEL_TYPE_CHOICES,
        blank=True,
        verbose_name="Type de carburant",
        help_text="Diesel, Essence, Électrique, Hybride, etc."
    )

    # Contrôle technique
    last_technical_inspection = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date du dernier contrôle technique",
        help_text="Format: JJ/MM/AAAA, ne peut pas être dans le futur de plus d'un an"
    )

    # Assurance (BF5)
    insurance_company = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nom de l'assurance",
        help_text="Max 100 caractères"
    )
    insurance_expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date d'échéance de l'assurance",
        help_text="Format: JJ/MM/AAAA"
    )

    # Notes optionnelles
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Informations additionnelles"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    is_active = models.BooleanField(default=True, verbose_name="Actif", help_text="Suppression logique")

    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ['-created_at']

    def __str__(self):
        identifier = self.plate_number if self.plate_number else self.nickname
        return f"{self.brand} {self.model} ({identifier})"

    def clean(self):
        """
        Validation personnalisée (BF5)
        - Au moins immatriculation OU surnom doit être fourni
        - Surnom min 2 caractères si fourni
        """
        super().clean()

        # Validation: au moins immat OU surnom
        if not self.plate_number and not self.nickname:
            raise ValidationError(
                "Vous devez fournir soit une immatriculation, soit un surnom pour le véhicule."
            )

        # Validation surnom si pas d'immat
        if not self.plate_number and self.nickname and len(self.nickname) < 2:
            raise ValidationError({
                'nickname': "Le surnom doit contenir au moins 2 caractères."
            })

        # Validation marque/modèle longueur
        if len(self.brand) < 2:
            raise ValidationError({'brand': "La marque doit contenir au moins 2 caractères."})

        if len(self.model) < 2:
            raise ValidationError({'model': "Le modèle doit contenir au moins 2 caractères."})

        # Validation date CT
        if self.last_technical_inspection:
            from datetime import timedelta
            max_future = datetime.now().date() + timedelta(days=365)
            if self.last_technical_inspection > max_future:
                raise ValidationError({
                    'last_technical_inspection': "La date du contrôle technique ne peut pas être dans le futur de plus d'un an."
                })

    def save(self, *args, **kwargs):
        """Override save pour appeler clean()"""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_identifier(self):
        """Retourne l'identifiant du véhicule (immat ou surnom)"""
        return self.plate_number if self.plate_number else self.nickname


class VehicleHistory(models.Model):
    """
    Historique des événements liés à un véhicule
    Utilisé pour traçabilité et consultation historique
    """
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='history', verbose_name="Véhicule")
    event_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de l'événement")
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('CREATION', 'Création du véhicule'),
            ('MODIFICATION', 'Modification'),
            ('DELETE', 'Suppression (Désactivation)'),
            ('ACTIVATION', 'Activation'),
            ('CASE_CREATED', 'Nouveau dossier'),
            ('QUOTE_GENERATED', 'Devis généré'),
            ('REPAIR_COMPLETED', 'Réparation terminée'),
            ('OTHER', 'Autre'),
        ],
        default='OTHER',
        verbose_name="Type d'événement"
    )
    description = models.TextField(verbose_name="Description")

    class Meta:
        verbose_name = "Historique Véhicule"
        verbose_name_plural = "Historiques Véhicules"
        ordering = ['-event_date']

    def __str__(self):
        return f"{self.vehicle} - {self.get_event_type_display()} ({self.event_date.strftime('%d/%m/%Y')})"
