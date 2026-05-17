from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Role, User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email ou identifiant",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "votre@email.com",
        })
    )

    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "••••••••",
        })
    )


class ClientSignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "jean.dupont@email.com",
        })
    )

    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "+212 6 12 34 56 78",
        })
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "password1",
            "password2",
        )

        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "jeandupont",
            }),
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Jean",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Dupont",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "••••••••",
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "••••••••",
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = Role.CLIENT

        if commit:
            user.save()

        return user


class StaffSignupForm(ClientSignupForm):
    token = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Token staff",
        })
    )

    role = forms.ChoiceField(
        choices=[
            choice for choice in Role.choices
            if choice[0] not in (Role.CLIENT, Role.ADMIN)
        ],
        widget=forms.Select(attrs={
            "class": "form-control",
        })
    )

    def __init__(self, *args, allowed_role=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.allowed_role = allowed_role

        if allowed_role:
            self.fields["role"].initial = allowed_role
            self.fields["role"].disabled = True

    def clean_token(self):
        import os

        token = self.cleaned_data.get("token")

        if token != os.getenv("STAFF_SIGNUP_TOKEN", "dev-token"):
            raise forms.ValidationError("Token invalide")

        return token

    def save(self, commit=True):
        user = UserCreationForm.save(self, commit=False)
        user.role = self.allowed_role or self.cleaned_data["role"]

        if commit:
            user.save()

        return user