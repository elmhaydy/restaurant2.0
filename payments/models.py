from django.db import models
from orders.models import Order
class Payment(models.Model):
 CASH='CASH'; CARD='CARD'; ONLINE='ONLINE'; METHODS=[(CASH,'Espèces'),(CARD,'Carte bancaire'),(ONLINE,'En ligne')]
 order=models.OneToOneField(Order,on_delete=models.PROTECT,related_name='payment'); method=models.CharField(max_length=20,choices=METHODS); amount=models.DecimalField(max_digits=10,decimal_places=2); created_at=models.DateTimeField(auto_now_add=True)
class CashClosure(models.Model):
 date=models.DateField(unique=True); expected_amount=models.DecimalField(max_digits=10,decimal_places=2); real_amount=models.DecimalField(max_digits=10,decimal_places=2); note=models.TextField(blank=True)
