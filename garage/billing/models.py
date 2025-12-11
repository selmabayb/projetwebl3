# garage/billing/models.py

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class Invoice(models.Model):
    """
    Facture générée pour un dossier
    BF32-34: Génération facture avec numérotation automatique
    """
    # Relation au dossier
    case = models.OneToOneField(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='invoice',
        verbose_name="Dossier"
    )

    # Référence au devis associé
    related_quote = models.ForeignKey(
        'quotes.Quote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Devis associé"
    )

    # Numérotation (FAC-YYYY-###)
    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Numéro de facture",
        help_text="Format: FAC-YYYY-###"
    )

    # Montants (identiques au devis validé)
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
        verbose_name="Taux TVA"
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

    # Paiement
    is_paid = models.BooleanField(default=False, verbose_name="Payée")
    payment_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de paiement"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'émission")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.total_ttc}€ TTC"

    def save(self, *args, **kwargs):
        """Override save pour générer le numéro de facture (BF33)"""
        if not self.invoice_number:
            # Génération du numéro FAC-YYYY-###
            year = timezone.now().year
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=f'FAC-{year}-'
            ).order_by('-invoice_number').first()

            if last_invoice:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.invoice_number = f'FAC-{year}-{new_num:03d}'

        super().save(*args, **kwargs)


class InvoiceLine(models.Model):
    """
    Ligne de facture (identique aux lignes de devis)
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines', verbose_name="Facture")
    description = models.CharField(max_length=200, verbose_name="Description")
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Quantité")
    unit_price_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix unitaire HT (€)"
    )
    total_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total HT (€)"
    )

    class Meta:
        verbose_name = "Ligne de Facture"
        verbose_name_plural = "Lignes de Facture"
        ordering = ['id']

    def __str__(self):
        return f"{self.description} - {self.total_ht}€ HT"

    def save(self, *args, **kwargs):
        """Calcule le total HT automatiquement"""
        self.total_ht = self.quantity * self.unit_price_ht
        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    Paiement effectué pour une facture
    """
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Espèces'),
        ('CARD', 'Carte bancaire'),
        ('CHECK', 'Chèque'),
        ('TRANSFER', 'Virement'),
        ('OTHER', 'Autre'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('COMPLETED', 'Complété'),
        ('FAILED', 'Échoué'),
        ('REFUNDED', 'Remboursé'),
    ]

    # Relations
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Facture"
    )

    # Informations paiement
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Montant (€)"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='CARD',
        verbose_name="Méthode de paiement"
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING',
        verbose_name="Statut"
    )

    # Référence transaction
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID Transaction",
        help_text="Référence externe (ex: Stripe, PayPal)"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de complétion"
    )

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']

    def __str__(self):
        return f"Paiement {self.amount}€ - {self.get_status_display()}"
