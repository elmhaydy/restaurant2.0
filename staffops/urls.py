from django.urls import path
from . import views

app_name = 'staffops'

urlpatterns = [
    path('manager/', views.manager_dashboard, name='manager_dashboard'),

    path('chef/', views.chef, name='chef'),
    path('chef/order/<int:pk>/<str:status>/', views.update_order_status, name='order_status'),

    path('caissier/', views.caissier, name='caissier'),
    path('caissier/order/<int:order_id>/pay/', views.caissier_pay_order, name='caissier_pay_order'),
    
    path('menage/', views.menage, name='menage'),
    path('menage/task/<int:pk>/done/', views.task_done, name='task_done'),

    path('serveur/', views.serveur, name='serveur'),
    path('serveur/table/<int:table_id>/', views.serveur_table_detail, name='serveur_table_detail'),
    path('serveur/table/<int:table_id>/order/add/', views.serveur_add_order_item, name='serveur_add_order_item'),
    path('serveur/order/<int:order_id>/send/', views.serveur_send_order, name='serveur_send_order'),
    path('serveur/order/<int:order_id>/served/', views.serveur_mark_served, name='serveur_mark_served'),
    path('serveur/order/<int:order_id>/bill/', views.serveur_request_bill, name='serveur_request_bill'),

    path('livreur/', views.livreur, name='livreur'),
    path('livreur/order/<int:pk>/<str:status>/', views.update_delivery_status, name='delivery_status'),

    path('profil/', views.staff_profile, name='staff_profile'),

    path('payments/', views.staff_payments, name='staff_payments'),
    path('commandes/', views.commandes_history, name='commandes_history'),
]