from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.menu_list, name='list'),
    path('plat/<slug:slug>/', views.dish_detail, name='detail'),
]