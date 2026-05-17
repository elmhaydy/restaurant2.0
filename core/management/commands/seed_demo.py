from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from menu.models import Category,Dish
from reservations.models import RestaurantTable
class Command(BaseCommand):
 def handle(self,*a,**kw):
  U=get_user_model()
  for username,role in [('admin','ADMIN'),('chef','CHEF'),('caissier','CAISSIER'),('menage','MENAGE'),('client','CLIENT')]:
   u,created=U.objects.get_or_create(username=username,defaults={'role':role,'email':username+'@demo.ma','is_staff':role=='ADMIN','is_superuser':role=='ADMIN'})
   if created: u.set_password('Pass12345!'); u.save()
  cat,_=Category.objects.get_or_create(name='Plats marocains',slug='plats-marocains')
  Dish.objects.get_or_create(category=cat,name='Tajine Poulet Citron',slug='tajine-poulet-citron',defaults={'price':75,'description':'Tajine traditionnel parfumé.'})
  Dish.objects.get_or_create(category=cat,name='Couscous Royal',slug='couscous-royal',defaults={'price':90,'description':'Couscous du vendredi.'})
  for n,c in [(1,4),(2,4),(3,6),(4,2)]: RestaurantTable.objects.get_or_create(number=n,defaults={'capacity':c})
  self.stdout.write(self.style.SUCCESS('Demo OK. Mot de passe: Pass12345!'))
