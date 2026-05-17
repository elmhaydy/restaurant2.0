from django.db import models
from django.conf import settings

class CleaningTask(models.Model):
    TODO='TODO'; 
    DOING='DOING'; 
    DONE='DONE'; 
    STATUS=[
        (TODO,'À faire'),
        (DOING,'En cours'),
        (DONE,'Terminé')
    ]

    employee=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True);
    zone=models.CharField(max_length=100); 
    title=models.CharField(max_length=160);
    scheduled_at=models.DateTimeField(); 
    status=models.CharField(max_length=20,choices=STATUS,default=TODO); 
    completed_at=models.DateTimeField(null=True,blank=True)




class StaffPayment(models.Model):
    CASH = 'CASH'
    BANK = 'BANK'
    CHECK = 'CHECK'

    METHODS = [
        (CASH, 'Espèces'),
        (BANK, 'Virement bancaire'),
        (CHECK, 'Chèque'),
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHODS, default=CASH)
    period = models.CharField(max_length=100)
    note = models.TextField(blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_payments_done'
    )

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.employee} - {self.amount} MAD'
    

class CashPayment(models.Model):
    CASH = 'CASH'
    CARD = 'CARD'

    METHODS = [
        (CASH, 'Espèces'),
        (CARD, 'Carte bancaire'),
    ]

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='cash_payment'
    )
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHODS)
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f'Facture #{self.order.id} - {self.amount} MAD'