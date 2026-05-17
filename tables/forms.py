from django import forms
from .models import RestaurantTable

class RestaurantTableForm(forms.ModelForm):
    class Meta:
        model = RestaurantTable
        fields = [
            "name",
            "number",
            "zone",
            "capacity",
            "status",
            "pos_x",
            "pos_y",
            "is_active",
            "notes",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "number": forms.NumberInput(attrs={"class": "form-control"}),
            "zone": forms.Select(attrs={"class": "form-control"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "pos_x": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100}),
            "pos_y": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }