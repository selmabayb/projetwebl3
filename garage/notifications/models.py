# garage/notifications/models.py

from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    """
    Notification in-app pour les clients
    BF48, BF50: Centre de notifications avec badge compteur
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('INFO', 'Information'),
        ('SUCCESS', 'Succès'),
        ('WARNING', 'Avertissement'),
        ('ERROR', 'Erreur'),
    ]

    # Destinataire
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinataire"
    )

    # Contenu
    title = models.CharField(max_length=100, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='INFO',
        verbose_name="Type"
    )

    # Lien vers le dossier concerné (optionnel)
    related_case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='notifications',
        verbose_name="Dossier concerné"
    )

    # Statut
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    read_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Lu le"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        status = "✓" if self.is_read else "●"
        return f"{status} {self.title} - {self.user.username}"

    def mark_as_read(self):
        """Marque la notification comme lue"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    @classmethod
    def create_for_case_status_change(cls, case, new_status):
        """
        Crée une notification lors d'un changement de statut (BF50)
        """
        status_messages = {
            'DEVIS_EMIS': {
                'title': 'Votre devis est prêt',
                'message': f'Le devis pour votre {case.vehicle} est disponible. Montant: {case.quote.total_ttc}€ TTC. Valable jusqu\'au {case.quote.validity_date.strftime("%d/%m/%Y")}.' if hasattr(case, 'quote') else f'Le devis pour votre {case.vehicle} est disponible.',
                'type': 'SUCCESS',
            },
            'DEVIS_ACCEPTE': {
                'title': 'Devis accepté',
                'message': f'Vous avez accepté le devis. Vous pouvez maintenant réserver un rendez-vous.',
                'type': 'INFO',
            },
            'RDV_CONFIRME': {
                'title': 'Rendez-vous confirmé',
                'message': f'Votre rendez-vous est confirmé pour le {case.appointment.date.strftime("%d/%m/%Y")} à {case.appointment.start_time if isinstance(case.appointment.start_time, str) else case.appointment.start_time.strftime("%H:%M")}.' if hasattr(case, 'appointment') else 'Votre rendez-vous est confirmé.',
                'type': 'SUCCESS',
            },
            'EN_COURS': {
                'title': 'Intervention en cours',
                'message': f'Les réparations de votre {case.vehicle} ont commencé.',
                'type': 'INFO',
            },
            'PRET': {
                'title': 'Votre véhicule est prêt !',
                'message': f'Les réparations de votre {case.vehicle} sont terminées. Vous pouvez venir récupérer votre véhicule.',
                'type': 'SUCCESS',
            },
            'CLOTURE': {
                'title': 'Dossier clôturé',
                'message': f'Votre dossier a été clôturé. Merci de votre confiance !',
                'type': 'INFO',
            },
        }

        if new_status in status_messages:
            notif_data = status_messages[new_status]
            cls.objects.create(
                user=case.client,
                title=notif_data['title'],
                message=notif_data['message'],
                notification_type=notif_data['type'],
                related_case=case
            )

    @classmethod
    def get_unread_count(cls, user):
        """Retourne le nombre de notifications non lues pour le badge (BF48)"""
        return cls.objects.filter(user=user, is_read=False).count()

    @classmethod
    def _get_managers(cls):
        """Retourne tous les utilisateurs gestionnaires et admins"""
        from garage.accounts.models import UserProfile
        return User.objects.filter(
            profile__role__in=['GESTIONNAIRE', 'ADMIN']
        )

    @classmethod
    def notify_managers_new_case(cls, case):
        """
        Notifie les gestionnaires qu'un nouveau dossier a été créé
        """
        managers = cls._get_managers()
        for manager in managers:
            cls.objects.create(
                user=manager,
                title='Nouveau dossier créé',
                message=f'Un nouveau dossier a été créé par {case.client.get_full_name() or case.client.username} pour le véhicule {case.vehicle}.',
                notification_type='INFO',
                related_case=case
            )

    @classmethod
    def notify_managers_quote_accepted(cls, case):
        """
        Notifie les gestionnaires qu'un client a accepté un devis
        """
        managers = cls._get_managers()
        for manager in managers:
            cls.objects.create(
                user=manager,
                title='Devis accepté par un client',
                message=f'{case.client.get_full_name() or case.client.username} a accepté le devis pour le dossier #{case.id} ({case.vehicle}).',
                notification_type='SUCCESS',
                related_case=case
            )

    @classmethod
    def notify_managers_appointment_created(cls, appointment):
        """
        Notifie les gestionnaires qu'un client a pris un rendez-vous
        """
        managers = cls._get_managers()
        case = appointment.case
        date_str = appointment.date.strftime("%d/%m/%Y")
        time_str = appointment.start_time.strftime("%H:%M") if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)

        for manager in managers:
            cls.objects.create(
                user=manager,
                title='Nouveau rendez-vous pris',
                message=f'{case.client.get_full_name() or case.client.username} a pris rendez-vous le {date_str} à {time_str} pour le dossier #{case.id} ({case.vehicle}).',
                notification_type='SUCCESS',
                related_case=case
            )

    @classmethod
    def notify_managers_appointment_modified(cls, appointment):
        """
        Notifie les gestionnaires qu'un client a modifié un rendez-vous
        """
        managers = cls._get_managers()
        case = appointment.case
        date_str = appointment.date.strftime("%d/%m/%Y")
        time_str = appointment.start_time.strftime("%H:%M") if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)

        for manager in managers:
            cls.objects.create(
                user=manager,
                title='Rendez-vous modifié',
                message=f'{case.client.get_full_name() or case.client.username} a modifié son rendez-vous. Nouvelle date: {date_str} à {time_str} (dossier #{case.id}).',
                notification_type='WARNING',
                related_case=case
            )

    @classmethod
    def notify_managers_appointment_cancelled(cls, appointment):
        """
        Notifie les gestionnaires qu'un client a annulé un rendez-vous
        """
        managers = cls._get_managers()
        case = appointment.case
        date_str = appointment.date.strftime("%d/%m/%Y")
        time_str = appointment.start_time.strftime("%H:%M") if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)

        for manager in managers:
            cls.objects.create(
                user=manager,
                title='Rendez-vous annulé',
                message=f'{case.client.get_full_name() or case.client.username} a annulé son rendez-vous du {date_str} à {time_str} (dossier #{case.id}). Motif: {appointment.cancellation_reason or "Non spécifié"}',
                notification_type='WARNING',
                related_case=case
            )
