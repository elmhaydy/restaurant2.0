from django import forms
from .models import Order
class CheckoutForm(forms.ModelForm):
 class Meta: model=Order; fields=['mode','customer_name','phone','delivery_address','notes']
