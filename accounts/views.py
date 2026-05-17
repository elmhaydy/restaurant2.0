from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from django.urls import reverse_lazy

from .forms import ClientSignupForm, LoginForm, StaffSignupForm
from .models import Role


class AppLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm

    def get_success_url(self):
        return reverse_lazy('accounts:redirect')


class AppLogoutView(LogoutView):
    next_page = 'home'


def signup_client(request):
    form = ClientSignupForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('accounts:redirect')

    return render(request, 'accounts/signup.html', {
        'form': form,
        'title': 'Inscription client',
    })


def signup_staff(request, role):
    role = role.upper()
    form = StaffSignupForm(request.POST or None, allowed_role=role)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('accounts:redirect')

    return render(request, 'accounts/signup.html', {
        'form': form,
        'title': f'Inscription staff {role}',
    })


@login_required
def profile_view(request):
    from orders.models import Order
    from reservations.models import Reservation
    return render(request, 'accounts/profile.html', {
        'recent_orders': Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')[:8],
        'recent_reservations': Reservation.objects.filter(user=request.user).select_related('table').order_by('-date', '-time')[:8],
    })


@login_required
def role_redirect(request):
    user = request.user
    role = user.role

    if user.is_superuser or role == Role.ADMIN:
        return redirect('admin_panel:home')
    if role == Role.MANAGER:
        return redirect('staffops:manager_dashboard')

    if role == Role.CHEF:
        return redirect('staffops:chef')

    if role == Role.CAISSIER:
        return redirect('staffops:caissier')

    if role == Role.MENAGE:
        return redirect('staffops:menage')

    if role == Role.SERVEUR:
        return redirect('staffops:serveur')
    
    if role == Role.LIVREUR:
        return redirect('staffops:livreur')

    return redirect('orders:my_orders')