# garage/quotes/models.py

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta


class Quote(models.Model):
    """
    Devis généré automatiquement pour un dossier
    BF12-14, BF26-28: Génération et gestion des devis
    Section 6.4: Calcul du devis
    """
    # Relation au dossier
    case = models.OneToOneField(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='quote',
        verbose_name="Dossier"
    )

    # Numérotation (DEV-YYYY-###)
    quote_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Numéro de devis",
        help_text="Format: DEV-YYYY-###"
    )

    # Montants détaillés (BF13)
    total_labor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total Main d'Œuvre HT (€)"
    )

    total_parts = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total Pièces HT (€)"
    )

    total_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total HT (€)"
    )

    vat_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.20'),
        verbose_name="Taux TVA",
        help_text="Ex: 0.20 pour 20%"
    )

    total_vat = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant TVA (€)"
    )

    total_ttc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total TTC (€)"
    )

    # Validité (BF13, Section 6.4.2)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'émission")
    validity_date = models.DateField(
        verbose_name="Date de validité",
        help_text="Date limite d'acceptation (+15 jours)"
    )

    # États du devis
    is_validated_by_manager = models.BooleanField(
        default=False,
        verbose_name="Validé par gestionnaire",
        help_text="Verrouillé après validation gestionnaire (BF27)"
    )

    is_accepted_by_client = models.BooleanField(
        default=False,
        verbose_name="Accepté par le client",
        help_text="Client a accepté le devis (BF44)"
    )

    is_refused_by_client = models.BooleanField(
        default=False,
        verbose_name="Refusé par le client"
    )

    refusal_reason = models.TextField(
        blank=True,
        verbose_name="Motif de refus",
        help_text="Motif optionnel si refusé (BF45)"
    )

    acceptance_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date d'acceptation"
    )

    # Métadonnées
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Devis"
        verbose_name_plural = "Devis"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.quote_number} - {self.total_ttc}€ TTC"

    def save(self, *args, **kwargs):
        """Override save pour calculer validity_date et quote_number"""
        if not self.validity_date:
            # +15 jours par défaut (Section 6.4.2)
            from django.conf import settings
            days = getattr(settings, 'GARAGE_QUOTE_VALIDITY_DAYS', 15)
            self.validity_date = (timezone.now() + timedelta(days=days)).date()

        if not self.quote_number:
            # Génération du numéro DEV-YYYY-###
            year = timezone.now().year
            last_quote = Quote.objects.filter(
                quote_number__startswith=f'DEV-{year}-'
            ).order_by('-quote_number').first()

            if last_quote:
                last_num = int(last_quote.quote_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.quote_number = f'DEV-{year}-{new_num:03d}'

        super().save(*args, **kwargs)

    def is_expired(self):
        """Vérifie si le devis est expiré (Section 6.4.2)"""
        return timezone.now().date() > self.validity_date and not self.is_accepted_by_client

    def can_be_modified(self):
        """Vérifie si le devis peut être modifié (BF26)"""
        return not self.is_accepted_by_client and not self.is_validated_by_manager

    def calculate_totals(self):
        """Recalcule tous les totaux (BF28, Section 6.4)"""
        lines = self.lines.all()

        self.total_labor = sum(
            line.total_ht for line in lines if line.line_type == 'LABOR'
        )
        self.total_parts = sum(
            line.total_ht for line in lines if line.line_type == 'PARTS'
        )
        self.total_ht = self.total_labor + self.total_parts
        self.total_vat = self.total_ht * self.vat_rate
        self.total_ttc = self.total_ht + self.total_vat

        self.save()


class QuoteLine(models.Model):
    """
    Ligne de devis (Main d'œuvre ou Pièce)
    Utilisé pour détailler le devis
    """
    LINE_TYPE_CHOICES = [
        ('LABOR', 'Main d\'œuvre'),
        ('PARTS', 'Pièces'),
    ]

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='lines', verbose_name="Devis")
    line_type = models.CharField(max_length=10, choices=LINE_TYPE_CHOICES, verbose_name="Type de ligne")

    # Description
    description = models.CharField(max_length=200, verbose_name="Description")

    # Pour la main d'œuvre
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Heures",
        help_text="Nombre d'heures de main d'œuvre"
    )
    hourly_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Taux horaire (€/h)"
    )

    # Pour les pièces
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Quantité"
    )
    unit_price_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix unitaire HT (€)"
    )

    # Total HT de la ligne
    total_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total HT (€)"
    )

    class Meta:
        verbose_name = "Ligne de Devis"
        verbose_name_plural = "Lignes de Devis"
        ordering = ['line_type', 'id']

    def __str__(self):
        return f"{self.get_line_type_display()} - {self.description}"

    def save(self, *args, **kwargs):
        """Calcule le total HT automatiquement"""
        if self.line_type == 'LABOR' and self.hours and self.hourly_rate:
            self.total_ht = self.hours * self.hourly_rate
        elif self.line_type == 'PARTS':
            self.total_ht = self.quantity * self.unit_price_ht

        super().save(*args, **kwargs)
