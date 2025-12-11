# garage/quotes/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Quote, QuoteLine
from garage.cases.models import Case


class QuoteCreateForm(forms.ModelForm):
    """
    Formulaire pour créer un nouveau devis depuis un dossier
    Utilisé par les gestionnaires uniquement
    """
    class Meta:
        model = Quote
        fields = ['case']
        widgets = {
            'case': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'case': 'Dossier',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer uniquement les dossiers avec statut NOUVEAU et sans devis existant
        self.fields['case'].queryset = Case.objects.filter(
            status='NOUVEAU'
        ).exclude(
            quote__isnull=False
        )

    def clean_case(self):
        case = self.cleaned_data.get('case')

        # Vérifier que le dossier a des pannes sélectionnées
        if case and case.faults.count() == 0:
            raise ValidationError(
                "Ce dossier n'a aucune panne sélectionnée. "
                "Veuillez d'abord ajouter des pannes au dossier."
            )

        # Vérifier qu'il n'existe pas déjà un devis pour ce dossier
        if Quote.objects.filter(case=case).exists():
            raise ValidationError(
                "Un devis existe déjà pour ce dossier."
            )

        return case


class QuoteLineForm(forms.ModelForm):
    """
    Formulaire pour une ligne de devis individuelle
    """
    class Meta:
        model = QuoteLine
        fields = ['description', 'quantity', 'unit_price_ht']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Description de la prestation...'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '1'
            }),
            'unit_price_ht': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            })
        }
        labels = {
            'description': 'Description',
            'quantity': 'Quantité',
            'unit_price_ht': 'Prix unitaire HT (€)',
        }


class QuoteAcceptForm(forms.Form):
    """
    Formulaire pour qu'un client accepte un devis
    """
    accept_terms = forms.BooleanField(
        required=True,
        label="J'accepte les conditions de ce devis et autorise les travaux",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={
            'required': 'Vous devez accepter les conditions pour continuer.'
        }
    )


class QuoteRefuseForm(forms.Form):
    """
    Formulaire pour qu'un client refuse un devis
    """
    reason = forms.CharField(
        required=False,
        label="Motif du refus (optionnel)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Indiquez la raison du refus si vous le souhaitez...'
        })
    )


class QuoteValidateForm(forms.Form):
    """
    Formulaire pour valider et émettre un devis (gestionnaire uniquement)
    """
    confirm = forms.BooleanField(
        required=True,
        label="Je confirme l'émission de ce devis au client",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={
            'required': 'Vous devez confirmer pour émettre le devis.'
        }
    )
