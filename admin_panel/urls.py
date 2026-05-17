from django.urls import path
from . import views
app_name='admin_panel'
urlpatterns=[
    path('',views.home,name='home'),
    path("profile/",views.admin_profile,name="admin_profile"),
    path('menu/', views.menu_admin, name='menu_admin'),
    # crud_menu
    # path('menu-crud/', views.menu_crud_list, name='menu_crud'),

    path("categories/", views.categories, name="categories"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:category_id>/update/", views.category_update, name="category_update"),
    path("categories/<int:category_id>/delete/", views.category_delete, name="category_delete"),
    
    path('menu/add/', views.dish_create, name='dish_create'),
    path('menu/<int:dish_id>/edit/', views.dish_update, name='dish_update'),
    path('menu/<int:dish_id>/delete/', views.dish_delete, name='dish_delete'),


    path("orders/", views.orders, name="orders"),
    path("orders/<int:order_id>/status/", views.order_update_status, name="order_update_status"),
    path("orders/<int:order_id>/delete/", views.order_delete, name="order_delete"),


    

    path("reservations/", views.reservations, name="reservations"),
    path("reservations/create/", views.reservation_create, name="reservation_create"),
    path("reservations/<int:reservation_id>/update/", views.reservation_update, name="reservation_update"),
    path("reservations/<int:reservation_id>/delete/", views.reservation_delete, name="reservation_delete"),
    path("reservations/<int:reservation_id>/confirm/", views.reservation_confirm, name="reservation_confirm"),
    path("reservations/<int:reservation_id>/seated/", views.reservation_mark_seated, name="reservation_mark_seated"),
    path("reservations/<int:reservation_id>/done/", views.reservation_mark_done, name="reservation_mark_done"),
  

    path('staff/', views.staff, name='staff'),
    path('settings/', views.settings_view, name='settings'),
    path('stock/', views.stock, name='stock'),
    
    path('staff/add/', views.staff_create, name='staff_create'),
    path('staff/<int:user_id>/edit/', views.staff_update, name='staff_update'),
    path('staff/<int:user_id>/delete/', views.staff_delete, name='staff_delete'),
    path('staff/<int:user_id>/pay/', views.staff_payment_create, name='staff_payment_create'),
    path('staff/<int:user_id>/payments/', views.staff_payment_history, name='staff_payment_history'),

    path('stock/add/', views.ingredient_create, name='ingredient_create'),
    path('stock/categories/create/', views.ingredient_category_create, name='ingredient_category_create'),
    path('stock/categories/<int:category_id>/edit/', views.ingredient_category_update, name='ingredient_category_update'),
    path('stock/categories/<int:category_id>/delete/', views.ingredient_category_delete, name='ingredient_category_delete'),
    path('stock/<int:ingredient_id>/edit/', views.ingredient_update, name='ingredient_update'),
    path('stock/<int:ingredient_id>/delete/', views.ingredient_delete, name='ingredient_delete'),

    path("logs/", views.logs_view, name="logs"),


    path("tables/", views.tables, name="tables"),
    path("tables/create/", views.table_create, name="table_create"),
    path("tables/<int:table_id>/reposition/", views.table_reposition, name="table_reposition"),
    path("tables/<int:table_id>/update/", views.table_update, name="table_update"),
    path("tables/<int:table_id>/delete/", views.table_delete, name="table_delete"),
    path("tables/<int:table_id>/status/", views.table_change_status, name="table_change_status"),
    
    ]
