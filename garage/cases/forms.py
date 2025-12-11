# garage/cases/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Case
from garage.vehicles.models import Vehicle
from garage.catalog.models import FaultGroup, Fault


class CaseCreateForm(forms.ModelForm):
    """
    Formulaire pour créer un nouveau dossier de réparation
    BF20: Le client peut déclarer un problème
    """

    class Meta:
        model = Case
        fields = ['vehicle', 'description', 'urgency_level']
        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez le problème rencontré avec votre véhicule...',
                'required': True
            }),
            'urgency_level': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'vehicle': 'Véhicule concerné',
            'description': 'Description du problème',
            'urgency_level': 'Niveau d\'urgence'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtrer les véhicules pour n'afficher que ceux de l'utilisateur
        if self.user:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(
                owner=self.user,
                is_active=True
            )

        # Rendre l'urgency_level optionnel (sera défini à NORMALE par défaut)
        self.fields['urgency_level'].required = False


    def save(self, commit=True):
        """
        Créer un nouveau dossier avec statut initial NOUVEAU
        """
        case = super().save(commit=False)

        # Définir le statut initial
        case.status = 'NOUVEAU'

        # Définir le client
        if self.user:
            case.client = self.user

        if commit:
            case.save()

        return case


class CaseCreateManagerForm(forms.ModelForm):
    """
    Formulaire pour créer un dossier en tant que gestionnaire.
    Permet de sélectionner n'importe quel véhicule.
    """
    class Meta:
        model = Case
        fields = ['vehicle', 'description', 'urgency_level']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description du problème...'
            }),
            'urgency_level': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Afficher tous les véhicules actifs, triés par propriétaire
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True).order_by('owner__username', 'brand')
        self.fields['vehicle'].label_from_instance = lambda obj: f"{obj.owner.username} - {obj.brand} {obj.model} ({obj.plate_number})"

    def save(self, commit=True):
        case = super().save(commit=False)
        case.status = 'NOUVEAU'
        # Le client est le propriétaire du véhicule
        if case.vehicle:
            case.client = case.vehicle.owner
        
        if commit:
            case.save()
        return case


class FaultSelectionForm(forms.Form):
    """
    Formulaire pour sélectionner les pannes depuis le catalogue
    BF21: Interface de sélection des pannes par groupes
    """
    fault_group = forms.ModelChoiceField(
        queryset=FaultGroup.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'fault-group-select'
        }),
        label='Groupe de pannes',
        required=False
    )

    faults = forms.ModelMultipleChoiceField(
        queryset=Fault.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Sélectionnez les pannes',
        required=False
    )

    def __init__(self, *args, **kwargs):
        case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)

        # Si un groupe est sélectionné, filtrer les pannes
        if self.data.get('fault_group'):
            try:
                group_id = int(self.data.get('fault_group'))
                self.fields['faults'].queryset = Fault.objects.filter(
                    group_id=group_id,
                    is_active=True
                )
            except (ValueError, TypeError):
                pass


class CaseSearchForm(forms.Form):
    """
    Formulaire de recherche/filtrage des dossiers
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par numéro de dossier, véhicule...'
        })
    )

    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + Case.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    urgency_level = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes les urgences')] + Case.URGENCY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class CaseUpdateStatusForm(forms.ModelForm):
    """
    Formulaire pour mettre à jour le statut d'un dossier (gestionnaire uniquement)
    """

    class Meta:
        model = Case
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limiter les transitions de statut possibles
        if self.instance and self.instance.pk:
            current_status = self.instance.status

            # Définir les transitions autorisées
            allowed_transitions = {
                'NOUVEAU': ['DEVIS_EMIS', 'EXPIRE'],
                'DEVIS_EMIS': ['DEVIS_ACCEPTE', 'DEVIS_REFUSE', 'EXPIRE'],
                'DEVIS_ACCEPTE': ['RDV_CONFIRME'],
                'RDV_CONFIRME': ['EN_COURS'],
                'EN_COURS': ['PRET'],
                'PRET': ['CLOTURE'],
                'DEVIS_REFUSE': [],
                'EXPIRE': [],
                'CLOTURE': []
            }

            # Filtrer les choix de statut
            allowed = allowed_transitions.get(current_status, [])
            if allowed:
                self.fields['status'].choices = [
                    (current_status, dict(Case.STATUS_CHOICES)[current_status])
                ] + [
                    (s, dict(Case.STATUS_CHOICES)[s]) for s in allowed
                ]
            else:
                self.fields['status'].widget.attrs['disabled'] = True
