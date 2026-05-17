from django import forms
from menu.models import Dish
from menu.models import Category
from accounts.models import User, Role
from staffops.models import StaffPayment
from stock.models import Ingredient, IngredientCategory


from .models import RestaurantSettings

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "is_active", "ordering"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "ordering": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = [
            'category',
            'name',
            'slug',
            'description',
            'price',
            'image',
            'is_active',
            'is_popular',
            'manual_available',
        ]

        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du plat'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: agneau-sept-heures'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check'}),
            'is_popular': forms.CheckboxInput(attrs={'class': 'form-check'}),
            'manual_available': forms.CheckboxInput(attrs={'class': 'form-check'}),
        }

class StaffCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_active', 'password']

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['role'].choices = [
            (Role.MANAGER, 'Manager'),
            (Role.SERVEUR, 'Serveur'),
            (Role.CHEF, 'Chef cuisinier'),
            (Role.CAISSIER, 'Caissier'),
            (Role.MENAGE, 'Femme de ménage'),
            (Role.LIVREUR, 'Livreur'),
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()

        return user


class StaffUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_active']

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['role'].choices = [
            (Role.MANAGER, 'Manager'),
            (Role.SERVEUR, 'Serveur'),
            (Role.CHEF, 'Chef cuisinier'),
            (Role.CAISSIER, 'Caissier'),
            (Role.MENAGE, 'Femme de ménage'),
            (Role.LIVREUR, 'Livreur'),
        ]


class StaffPaymentForm(forms.ModelForm):
    class Meta:
        model = StaffPayment
        fields = ['amount', 'method', 'period', 'note']

        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'method': forms.Select(attrs={'class': 'form-control'}),
            'period': forms.TextInput(attrs={'class': 'form-control', 'type': 'month'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = [
            "category",
            "name",
            "quantity",
            "unit",
            "unit_price",
            "alert_threshold",
        ]

        labels = {
            "category": "Catégorie",
            "name": "Nom de l'ingrédient",
            "quantity": "Quantité en stock",
            "unit": "Unité",
            "unit_price": "Prix unitaire",
            "alert_threshold": "Seuil d'alerte",
        }

        widgets = {
            "category": forms.Select(attrs={
                "class": "form-control"
            }),
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex: Farine T55"
            }),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "unit": forms.Select(attrs={
                "class": "form-control"
            }),
            "unit_price": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "Ex: 0.02"
            }),
            "alert_threshold": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
        }


class IngredientCategoryForm(forms.ModelForm):
    class Meta:
        model = IngredientCategory
        fields = ["name", "slug", "is_active", "ordering"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "ordering": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class RestaurantSettingsForm(forms.ModelForm):
    class Meta:
        model = RestaurantSettings
        fields = "__all__"
        widgets = {
            "restaurant_name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "max_reservation_people": forms.NumberInput(attrs={"class": "form-control"}),
            "service_fee_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
