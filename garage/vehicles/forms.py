# garage/vehicles/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Vehicle


class VehicleForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un véhicule
    BF10: Le client peut créer un ou plusieurs véhicules
    """
    fuel_type = forms.ChoiceField(
        choices=[('', '--- Sélectionnez ---')] + Vehicle.FUEL_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Vehicle
        fields = [
            'brand', 'model', 'year', 'plate_number', 'nickname',
            'mileage', 'fuel_type', 'last_technical_inspection',
            'insurance_company', 'insurance_expiry_date', 'notes'
        ]
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Renault'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Clio'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2020',
                'min': 1900
            }),
            'plate_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'AB-123-CD',
                'pattern': '[A-Z]{2}-[0-9]{3}-[A-Z]{2}'
            }),
            'nickname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Ma petite voiture'
            }),
            'mileage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '50000',
                'min': 0
            }),
            'fuel_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'last_technical_inspection': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'insurance_company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de votre assureur'
            }),
            'insurance_expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes additionnelles (optionnel)'
            })
        }
        help_texts = {
            'plate_number': 'Format: AB-123-CD. Laissez vide si vous utilisez un surnom.',
            'nickname': 'Nom personnalisé pour votre véhicule. Requis si pas d\'immatriculation.',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # L'immatriculation ET le surnom ne sont pas obligatoires individuellement
        # mais au moins l'un des deux doit être fourni (validation dans clean())
        self.fields['plate_number'].required = False
        self.fields['nickname'].required = False

    def clean(self):
        """
        Validation : au moins l'immatriculation OU le surnom doit être fourni
        """
        cleaned_data = super().clean()
        plate_number = cleaned_data.get('plate_number')
        nickname = cleaned_data.get('nickname')

        if not plate_number and not nickname:
            raise ValidationError(
                "Vous devez fournir soit une immatriculation, soit un surnom pour le véhicule."
            )

        return cleaned_data

    def save(self, commit=True):
        """
        Associe automatiquement le véhicule à l'utilisateur connecté
        """
        vehicle = super().save(commit=False)

        if self.user:
            vehicle.owner = self.user

        if commit:
            vehicle.save()

        return vehicle


class VehicleSearchForm(forms.Form):
    """
    Formulaire de recherche/filtrage des véhicules
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par marque, modèle, immatriculation ou surnom...'
        })
    )

    fuel_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les carburants')] + Vehicle.FUEL_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Tous'),
            ('true', 'Actifs seulement'),
            ('false', 'Inactifs seulement')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Statut'
    )
