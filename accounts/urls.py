from django.urls import path
from . import views

app_name='accounts'

urlpatterns=[
    path('login/',views.AppLoginView.as_view(),name='login'),
    path('logout/',views.AppLogoutView.as_view(),name='logout'),
    path('signup/client/',views.signup_client,name='signup_client'),
    path('signup/staff/<str:role>/',views.signup_staff,name='signup_staff'),
    path('profile/', views.profile_view, name='profile'),
    path('redirect/',views.role_redirect,name='redirect')]
