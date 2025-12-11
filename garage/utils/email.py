# garage/utils/email.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_email(subject, recipient_list, template_name, context, from_email=None):
    """
    Envoie un email HTML avec fallback texte

    Args:
        subject: Sujet de l'email
        recipient_list: Liste des destinataires
        template_name: Nom du template HTML (sans l'extension)
        context: Contexte pour le template
        from_email: Expéditeur (optionnel, utilise DEFAULT_FROM_EMAIL si non fourni)

    Returns:
        Nombre d'emails envoyés avec succès
    """
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL

    # Rendre le template HTML
    html_content = render_to_string(f'emails/{template_name}.html', context)

    # Créer une version texte depuis le HTML
    text_content = strip_tags(html_content)

    # Créer l'email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipient_list
    )

    # Attacher la version HTML
    email.attach_alternative(html_content, "text/html")

    # Envoyer l'email
    return email.send()


def send_quote_emitted_email(quote):
    """
    Envoie un email au client lorsqu'un devis est émis

    Args:
        quote: Instance du modèle Quote
    """
    subject = f"Votre devis {quote.quote_number} est disponible"
    recipient_list = [quote.case.client.email]

    context = {
        'quote': quote,
        'client': quote.case.client,
        'case': quote.case,
    }

    return send_email(subject, recipient_list, 'quote_emitted', context)


def send_quote_accepted_email(quote):
    """
    Envoie un email aux gestionnaires lorsqu'un devis est accepté

    Args:
        quote: Instance du modèle Quote
    """
    from garage.accounts.models import UserProfile

    subject = f"Devis {quote.quote_number} accepté par {quote.case.client.get_full_name()}"

    # Récupérer les emails des gestionnaires et admins
    managers = UserProfile.objects.filter(role__in=['GESTIONNAIRE', 'ADMIN'])
    recipient_list = [user.user.email for user in managers if user.user.email]

    if not recipient_list:
        return 0

    context = {
        'quote': quote,
        'client': quote.case.client,
        'case': quote.case,
    }

    return send_email(subject, recipient_list, 'quote_accepted', context)


def send_quote_refused_email(quote):
    """
    Envoie un email aux gestionnaires lorsqu'un devis est refusé

    Args:
        quote: Instance du modèle Quote
    """
    from garage.accounts.models import UserProfile

    subject = f"Devis {quote.quote_number} refusé par {quote.case.client.get_full_name()}"

    # Récupérer les emails des gestionnaires et admins
    managers = UserProfile.objects.filter(role__in=['GESTIONNAIRE', 'ADMIN'])
    recipient_list = [user.user.email for user in managers if user.user.email]

    if not recipient_list:
        return 0

    context = {
        'quote': quote,
        'client': quote.case.client,
        'case': quote.case,
        'refusal_reason': quote.refusal_reason,
    }

    return send_email(subject, recipient_list, 'quote_refused', context)


def send_appointment_confirmed_email(appointment):
    """
    Envoie un email de confirmation de rendez-vous au client

    Args:
        appointment: Instance du modèle Appointment
    """
    subject = f"Confirmation de votre rendez-vous du {appointment.date.strftime('%d/%m/%Y')}"
    recipient_list = [appointment.case.client.email]

    context = {
        'appointment': appointment,
        'client': appointment.case.client,
        'case': appointment.case,
    }

    return send_email(subject, recipient_list, 'appointment_confirmed', context)


def send_appointment_cancelled_email(appointment):
    """
    Envoie un email de confirmation d'annulation de rendez-vous

    Args:
        appointment: Instance du modèle Appointment
    """
    subject = f"Annulation de votre rendez-vous du {appointment.date.strftime('%d/%m/%Y')}"
    recipient_list = [appointment.case.client.email]

    context = {
        'appointment': appointment,
        'client': appointment.case.client,
        'case': appointment.case,
    }

    return send_email(subject, recipient_list, 'appointment_cancelled', context)


def send_appointment_reminder_email(appointment):
    """
    Envoie un email de rappel 24h avant le rendez-vous

    Args:
        appointment: Instance du modèle Appointment
    """
    subject = f"Rappel: Rendez-vous demain à {appointment.start_time.strftime('%H:%M')}"
    recipient_list = [appointment.case.client.email]

    context = {
        'appointment': appointment,
        'client': appointment.case.client,
        'case': appointment.case,
    }

    return send_email(subject, recipient_list, 'appointment_reminder', context)


def send_case_status_change_email(case, old_status, new_status):
    """
    Envoie un email au client lorsque le statut du dossier change

    Args:
        case: Instance du modèle Case
        old_status: Ancien statut
        new_status: Nouveau statut
    """
    subject = f"Mise à jour de votre dossier #{case.id}"
    recipient_list = [case.client.email]

    context = {
        'case': case,
        'client': case.client,
        'old_status': old_status,
        'new_status': new_status,
        'new_status_display': dict(case.STATUS_CHOICES).get(new_status, new_status),
    }

    return send_email(subject, recipient_list, 'case_status_change', context)
