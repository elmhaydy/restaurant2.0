from django import forms

from .models import Reservation
from tables.models import RestaurantTable, TableStatus

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = [
            "full_name",
            "email",
            "phone", 
            "date",
            "time",
            "guests",
            "table",
            "message"
        ]

        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "guests": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "id":"id_guests"
            }),
            "table": forms.Select(attrs={
                "class": "form-control",
                "id": "id_table",
            }),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        guests = kwargs.pop("guests",None)
        super().__init__(*args,**kwargs)

        tables = RestaurantTable.objects.filter(
            status = TableStatus.AVAILABLE,
            is_active=True,
        )

        if guests:
            tables = tables.filter(capacity__gte=guests)
        
        if self.is_bound:
           self.fields["table"].queryset = tables.order_by("zone", "capacity", "number")
        else:
           self.fields["table"].queryset = RestaurantTable.objects.none()
           
        self.fields["table"].required = True
        self.fields["table"].empty_label = "Choisir une table disponible"

class AdminReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["full_name", "email", "phone", "date", "time", "guests", "table", "status", "message"]

        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "guests": forms.NumberInput(attrs={"class": "form-control"}),
            "table": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        reservation = self.instance

        available_tables = RestaurantTable.objects.filter(
            is_active=True,
            capacity__gte=self.data.get("guests", reservation.guests or 1)
        ).exclude(status=TableStatus.OUT_OF_SERVICE)

        self.fields["table"].queryset = available_tables
