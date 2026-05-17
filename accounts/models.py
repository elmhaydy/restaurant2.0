from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrateur'
    MANAGER = 'MANAGER', 'Manager'
    CLIENT = 'CLIENT', 'Client'
    SERVEUR = 'SERVEUR', 'Serveur'
    CHEF = 'CHEF', 'Chef cuisinier'
    CAISSIER = 'CAISSIER', 'Caissier'
    MENAGE = 'MENAGE', 'Femme de ménage'
    LIVREUR = 'LIVREUR', 'Livreur'


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
        db_index=True
    )
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

    def is_role(self, *roles):
        return self.is_superuser or self.role in roles