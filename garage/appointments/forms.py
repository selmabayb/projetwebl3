# garage/appointments/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta, time
from .models import Appointment, AppointmentSlot
from garage.cases.models import Case


class AppointmentCreateForm(forms.ModelForm):
    """
    Formulaire pour créer un rendez-vous (client uniquement)
    Le client sélectionne une date et un créneau disponible
    """
    date = forms.DateField(
        label="Date du rendez-vous",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': (timezone.now().date() + timedelta(days=1)).isoformat()
        }),
        help_text="Sélectionnez une date (minimum 24h à l'avance)"
    )

    slot = forms.ModelChoiceField(
        queryset=AppointmentSlot.objects.none(),
        label="Créneau horaire",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Sélectionnez un créneau disponible"
    )

    class Meta:
        model = Appointment
        fields = ['date', 'slot']

    def __init__(self, *args, **kwargs):
        self.case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)

        # Le créneau sera chargé dynamiquement via JavaScript
        # basé sur la date sélectionnée
        self.fields['slot'].queryset = AppointmentSlot.objects.all()

    def clean_date(self):
        date = self.cleaned_data.get('date')

        if not date:
            raise ValidationError("La date est requise.")

        # Vérifier que c'est au moins 24h à l'avance
        min_date = timezone.now().date() + timedelta(days=1)
        if date < min_date:
            raise ValidationError(
                f"Le rendez-vous doit être réservé au moins 24h à l'avance. "
                f"Date minimum : {min_date.strftime('%d/%m/%Y')}"
            )

        return date

    def clean_slot(self):
        slot = self.cleaned_data.get('slot')

        if not slot:
            raise ValidationError("Vous devez sélectionner un créneau.")

        if not slot.is_available:
            raise ValidationError("Ce créneau n'est plus disponible.")

        return slot

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        slot = cleaned_data.get('slot')

        if date and slot:
            # Vérifier qu'il n'y a pas déjà un RDV à ce créneau
            existing = Appointment.objects.filter(
                date=date,
                start_time=slot.start_time,
                is_cancelled=False
            ).first()

            if existing:
                raise ValidationError(
                    "Ce créneau est déjà réservé pour cette date. "
                    "Veuillez choisir un autre créneau."
                )

        return cleaned_data

    def save(self, commit=True):
        appointment = super().save(commit=False)
        slot = self.cleaned_data['slot']

        # Affecter le dossier
        appointment.case = self.case

        # Copier les horaires du créneau
        appointment.start_time = slot.start_time
        appointment.end_time = slot.end_time

        if commit:
            appointment.save()

            # Mettre à jour le statut du dossier
            self.case.status = 'RDV_CONFIRME'
            self.case.save()

        return appointment


class AppointmentModifyForm(forms.ModelForm):
    """
    Formulaire pour modifier un rendez-vous existant
    """
    date = forms.DateField(
        label="Nouvelle date",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': (timezone.now().date() + timedelta(days=1)).isoformat()
        })
    )

    slot = forms.ModelChoiceField(
        queryset=AppointmentSlot.objects.none(),
        label="Nouveau créneau",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Appointment
        fields = ['date', 'slot']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Le créneau sera chargé dynamiquement via JavaScript
        # basé sur la date sélectionnée
        self.fields['slot'].queryset = AppointmentSlot.objects.all()

    def clean_date(self):
        date = self.cleaned_data.get('date')

        if not date:
            raise ValidationError("La date est requise.")

        # Vérifier que c'est au moins 24h à l'avance
        min_date = timezone.now().date() + timedelta(days=1)
        if date < min_date:
            raise ValidationError(
                f"Le rendez-vous doit être réservé au moins 24h à l'avance. "
                f"Date minimum : {min_date.strftime('%d/%m/%Y')}"
            )

        return date

    def clean_slot(self):
        slot = self.cleaned_data.get('slot')

        if not slot:
            raise ValidationError("Vous devez sélectionner un créneau.")

        if not slot.is_available:
            raise ValidationError("Ce créneau n'est plus disponible.")

        return slot

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        slot = cleaned_data.get('slot')

        if date and slot:
            # Vérifier qu'il n'y a pas déjà un RDV à ce créneau (sauf le nôtre)
            existing = Appointment.objects.filter(
                date=date,
                start_time=slot.start_time,
                is_cancelled=False
            ).exclude(pk=self.instance.pk).first()

            if existing:
                raise ValidationError(
                    "Ce créneau est déjà réservé pour cette date. "
                    "Veuillez choisir un autre créneau."
                )

        return cleaned_data

    def save(self, commit=True):
        appointment = super().save(commit=False)
        slot = self.cleaned_data['slot']

        # Copier les nouveaux horaires
        appointment.start_time = slot.start_time
        appointment.end_time = slot.end_time

        if commit:
            appointment.save()

        return appointment


class AppointmentCancelForm(forms.Form):
    """
    Formulaire pour annuler un rendez-vous
    """
    reason = forms.CharField(
        required=False,
        label="Motif de l'annulation (optionnel)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Indiquez la raison de l\'annulation si vous le souhaitez...'
        })
    )


class AppointmentSlotForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier des créneaux (admin uniquement)
    """
    class Meta:
        model = AppointmentSlot
        fields = [
            'is_recurring', 'weekday', 'date',
            'start_time', 'end_time',
            'is_available', 'is_exception'
        ]
        widgets = {
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'weekday': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_exception': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
