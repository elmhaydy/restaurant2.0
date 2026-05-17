from django.db import models
from django.conf import settings
class AuditLog(models.Model):
 user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True); action=models.CharField(max_length=100); path=models.CharField(max_length=255,blank=True); method=models.CharField(max_length=10,blank=True); ip_address=models.GenericIPAddressField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True)
 class Meta: ordering=['-created_at']
