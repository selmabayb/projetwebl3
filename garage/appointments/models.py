# garage/appointments/models.py

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta, time


class AppointmentSlot(models.Model):
    """
    Créneau de rendez-vous disponible
    BF43: Gérer les créneaux RDV (modèles récurrents + exceptions)
    """
    WEEKDAY_CHOICES = [
        (0, 'Lundi'),
        (1, 'Mardi'),
        (2, 'Mercredi'),
        (3, 'Jeudi'),
        (4, 'Vendredi'),
        (5, 'Samedi'),
        (6, 'Dimanche'),
    ]

    # Pour les créneaux récurrents
    is_recurring = models.BooleanField(
        default=False,
        verbose_name="Récurrent",
        help_text="Créneau récurrent (chaque semaine)"
    )
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        blank=True,
        null=True,
        verbose_name="Jour de la semaine",
        help_text="Pour les créneaux récurrents"
    )

    # Pour les créneaux ponctuels
    date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date spécifique",
        help_text="Pour un créneau ponctuel (non récurrent)"
    )

    # Horaire
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")

    # Disponibilité
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    is_exception = models.BooleanField(
        default=False,
        verbose_name="Exception",
        help_text="Jour férié ou fermeture exceptionnelle"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Créneau de RDV"
        verbose_name_plural = "Créneaux de RDV"
        ordering = ['weekday', 'start_time']

    def __str__(self):
        if self.is_recurring:
            return f"{self.get_weekday_display()} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        else:
            return f"{self.date.strftime('%d/%m/%Y')} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"

    def clean(self):
        """Validation: récurrent DOIT avoir weekday, ponctuel DOIT avoir date"""
        super().clean()

        if self.is_recurring and self.weekday is None:
            raise ValidationError("Un créneau récurrent doit avoir un jour de la semaine.")

        if not self.is_recurring and not self.date:
            raise ValidationError("Un créneau ponctuel doit avoir une date spécifique.")

        if self.start_time >= self.end_time:
            raise ValidationError("L'heure de début doit être avant l'heure de fin.")


class Appointment(models.Model):
    """
    Rendez-vous réservé par un client
    BF15-17, BF46-47: Réservation, modification, annulation
    """
    # Relations
    case = models.OneToOneField(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='appointment',
        verbose_name="Dossier"
    )

    # Date et heure du RDV
    date = models.DateField(verbose_name="Date du RDV")
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de réservation")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    # Statut
    is_cancelled = models.BooleanField(default=False, verbose_name="Annulé")
    cancellation_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date d'annulation"
    )
    cancellation_reason = models.TextField(
        blank=True,
        verbose_name="Motif d'annulation"
    )

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"RDV {self.case.client.get_full_name()} - {self.date.strftime('%d/%m/%Y')} à {self.start_time.strftime('%H:%M')}"

    def can_be_modified(self):
        """
        Vérifie si le RDV peut être modifié (BF46)
        Condition: > 24h avant le RDV
        """
        appointment_datetime = datetime.combine(self.date, self.start_time)
        now = timezone.now()
        hours_before = (appointment_datetime - now.replace(tzinfo=None)).total_seconds() / 3600

        from django.conf import settings
        min_hours = getattr(settings, 'GARAGE_APPOINTMENT_MIN_CANCEL_HOURS', 24)

        return hours_before > min_hours and not self.is_cancelled

    def can_be_cancelled(self):
        """
        Vérifie si le RDV peut être annulé (BF47)
        Condition: > 24h avant le RDV
        """
        return self.can_be_modified()

    def cancel(self, reason=""):
        """Annule le rendez-vous"""
        if not self.can_be_cancelled():
            raise ValidationError(
                "Impossible d'annuler un RDV moins de 24h avant l'heure prévue."
            )

        self.is_cancelled = True
        self.cancellation_date = timezone.now()
        self.cancellation_reason = reason
        self.save()

        # Remettre le statut du dossier à DEVIS_ACCEPTE (BF47)
        self.case.status = 'DEVIS_ACCEPTE'
        self.case.save()
