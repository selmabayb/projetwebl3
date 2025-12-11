from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=30, required=True, label="Nom")
    email = forms.EmailField(required=True, label="Adresse Email")
    phone_number = forms.CharField(max_length=20, required=False, label="Téléphone")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label="Adresse")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # UserProfile is created by signal, now update it
            if hasattr(user, 'profile'):
                user.profile.phone_number = self.cleaned_data['phone_number']
                user.profile.address = self.cleaned_data['address']
                user.profile.save()
        return user
