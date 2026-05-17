from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import F
from django.contrib.auth.decorators import login_required

from django.db.models import Sum

from accounts.models import Role
from .decorators import role_required
from .models import CleaningTask,CashPayment

from orders.models import Order,OrderItem
from menu.models import Dish
from tables.models import TableStatus

from .models import StaffPayment

try:
    from tables.models import RestaurantTable
except Exception:
    RestaurantTable = None

try:
    from reservations.models import Reservation
except Exception:
    Reservation = None

try:
    from stock.models import Ingredient
except Exception:
    Ingredient = None


@login_required
@role_required(Role.MANAGER)
def manager_dashboard(request):
    orders_count = Order.objects.count()
    active_orders = Order.objects.filter(
        status__in=[Order.PENDING, Order.PREPARING, Order.COOKING, Order.READY]
    ).count()

    tables_count = RestaurantTable.objects.count() if RestaurantTable else 0
    cleaning_count = CleaningTask.objects.filter(status=CleaningTask.TODO).count()

    reservations_today = 0
    if Reservation:
        reservations_today = Reservation.objects.filter(
            date=timezone.localdate()
        ).count()

    low_stock = []
    if Ingredient:
        low_stock = Ingredient.objects.filter(
            quantity__lte=F('alert_threshold')
        )[:5]

    return render(request, 'staff/manager.html', {
        'active_page': 'manager',
        'orders_count': orders_count,
        'active_orders': active_orders,
        'tables_count': tables_count,
        'cleaning_count': cleaning_count,
        'reservations_today': reservations_today,
        'low_stock': low_stock,
    })


@login_required
@role_required(Role.CHEF, Role.MANAGER)
def chef(request):
    orders = Order.objects.filter(
        status__in=[
            Order.PENDING,
            Order.PREPARING,
            Order.COOKING]
    ).prefetch_related('items__dish').order_by('created_at')

    return render(request, 'staff/chef.html', {
        'orders': orders,
        'active_page': 'chef',
    })


@login_required
@role_required(Role.CHEF, Role.MANAGER)
def update_order_status(request, pk, status):
    order = get_object_or_404(Order, pk=pk)

    allowed_statuses = [
        Order.PREPARING,
        Order.COOKING,
        Order.READY,
    ]

    if status in allowed_statuses:
        order.status = status
        order.save(update_fields=['status', 'updated_at'])

    return redirect('staffops:chef')


@login_required
@role_required(Role.CAISSIER, Role.MANAGER)
def caissier(request):
    today = timezone.localdate()

    orders = Order.objects.filter(
        mode=Order.ONSITE,
        status__in=[Order.BILL_REQUESTED, Order.SERVED]
    ).prefetch_related('items__dish').order_by('-updated_at')

    payments_today = CashPayment.objects.filter(
        paid_at__date=today
    ).select_related('order', 'cashier')

    # Total from all PAID orders today (works even without CashPayment record)
    paid_orders_today = Order.objects.filter(
        status=Order.PAID,
        updated_at__date=today
    ).prefetch_related('items')
    total_today = sum(o.total for o in paid_orders_today)

    cash_total_today = payments_today.filter(
        method=CashPayment.CASH
    ).aggregate(total=Sum('amount'))['total'] or 0

    card_total_today = payments_today.filter(
        method=CashPayment.CARD
    ).aggregate(total=Sum('amount'))['total'] or 0

    order_id = request.GET.get('order')
    selected_order = orders.filter(id=order_id).first() if order_id else orders.first()

    return render(request, 'staff/caissier.html', {
        'orders': orders,
        'selected_order': selected_order,
        'payments_today': payments_today,
        'total_today': total_today,
        'cash_total_today': cash_total_today,
        'card_total_today': card_total_today,
        'active_page': 'caissier',
    })

@login_required
@role_required(Role.CAISSIER, Role.MANAGER)
def caissier_pay_order(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        mode=Order.ONSITE,
        status__in=[Order.BILL_REQUESTED, Order.SERVED]
    )

    if request.method == 'POST':
        method = request.POST.get('method', CashPayment.CASH)

        CashPayment.objects.get_or_create(
            order=order,
            defaults={
                'cashier': request.user,
                'amount': order.total,
                'method': method,
            }
        )

        order.status = Order.PAID
        order.save(update_fields=['status', 'updated_at'])

        if order.table:
            order.table.status = TableStatus.NEEDS_CLEANING
            order.table.save(update_fields=['status'])

            CleaningTask.objects.get_or_create(
                title=f'Nettoyage {order.table.name}',
                status=CleaningTask.TODO,
                defaults={
                    'employee': None,
                    'zone': order.table.get_zone_display(),
                    'scheduled_at': timezone.now(),
                }
            )

    return redirect('staffops:caissier')

@login_required
@role_required(Role.MENAGE, Role.MANAGER)
def menage(request):
    # Créer automatiquement une tâche si une table est "à nettoyer"
    tables_to_clean = RestaurantTable.objects.filter(
        status=TableStatus.NEEDS_CLEANING,
        is_active=True
    )

    for table in tables_to_clean:
        CleaningTask.objects.get_or_create(
            title=f'Nettoyage {table.name}',
            status=CleaningTask.TODO,
            defaults={
                'employee': None,
                'zone': table.get_zone_display(),
                'scheduled_at': timezone.now(),
            }
        )

    tasks = CleaningTask.objects.filter(
        status__in=[CleaningTask.TODO, CleaningTask.DOING]
    ).order_by('scheduled_at')

    return render(request, 'staff/femme_menage.html', {
        'tasks': tasks,
        'now': timezone.now(),
        'active_page': 'menage',
    })

@login_required
@role_required(Role.MENAGE, Role.MANAGER)
def task_done(request, pk):
    if request.method != 'POST':
        return redirect('staffops:menage')

    task = get_object_or_404(CleaningTask, pk=pk)

    task.status = CleaningTask.DONE
    task.completed_at = timezone.now()
    task.save(update_fields=['status', 'completed_at'])

    for table in RestaurantTable.objects.filter(status=TableStatus.NEEDS_CLEANING):
        if table.name in task.title:
            table.status = TableStatus.AVAILABLE
            table.save(update_fields=['status'])
            break

    return redirect('staffops:menage')

@login_required
@role_required(Role.SERVEUR, Role.MANAGER)
def serveur(request):
    tables = RestaurantTable.objects.all().order_by('number') if RestaurantTable else []

    onsite_orders = Order.objects.filter(
        mode=Order.ONSITE,
        status__in=[
            Order.PENDING,
            Order.PREPARING,
            Order.COOKING,
            Order.READY,
            Order.SERVED,
            Order.BILL_REQUESTED,
        ]
    ).select_related('table').prefetch_related('items__dish')

    return render(request, 'staff/serveur.html', {
        'tables': tables,
        'onsite_orders': onsite_orders,
        'active_page': 'serveur',
    })


@login_required
@role_required(Role.SERVEUR, Role.MANAGER)
def serveur_table_detail(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)

    order = Order.objects.filter(
        table=table,
        mode=Order.ONSITE,
        status__in=[
            Order.PENDING,
            Order.PREPARING,
            Order.COOKING,
            Order.READY,
            Order.SERVED,
            Order.BILL_REQUESTED,
        ]
    ).prefetch_related('items__dish').first()

    dishes = Dish.objects.filter(
            is_active=True,
            manual_available=True
        ).order_by('category__name', 'name')

    return render(request, 'staff/serveur_table_detail.html', {
        'table': table,
        'order': order,
        'dishes': dishes,
        'active_page': 'serveur',
    })


@login_required
@role_required(Role.SERVEUR, Role.MANAGER)
def serveur_add_order_item(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)

    if request.method == 'POST':
        dish_id = request.POST.get('dish_id')
        quantity = int(request.POST.get('quantity', 1))

        dish = get_object_or_404(Dish, id=dish_id)

        order = Order.objects.filter(
            table=table,
            mode=Order.ONSITE,
            status__in=[
                Order.PENDING,
                Order.PREPARING,
                Order.COOKING,
                Order.READY,
                Order.SERVED,
                Order.BILL_REQUESTED,
            ]
        ).first()

        if not order:
            order = Order.objects.create(
                table=table,
                mode=Order.ONSITE,
                user=None,
                customer_name=f'Table {table.number}',
                status=Order.PENDING,
            )

        item, item_created = OrderItem.objects.get_or_create(
            order=order,
            dish=dish,
            defaults={
                'dish_name': dish.name,
                'quantity': quantity,
                'unit_price': dish.price,
            }
        )

        if not item_created:
            item.quantity += quantity
            item.save(update_fields=['quantity'])

        table.status = TableStatus.OCCUPIED
        table.save(update_fields=['status'])

    return redirect('staffops:serveur_table_detail', table_id=table.id)

@login_required
@role_required(Role.SERVEUR, Role.MANAGER)
def serveur_send_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, mode=Order.ONSITE)

    if order.status == Order.PENDING:
        order.status = Order.PREPARING
        order.save(update_fields=['status', 'updated_at'])

    return redirect('staffops:serveur_table_detail', table_id=order.table.id)


@login_required
@role_required(Role.SERVEUR, Role.MANAGER)
def serveur_mark_served(request, order_id):
    order = get_object_or_404(Order, id=order_id, mode=Order.ONSITE)

    if order.status == Order.READY:
        order.status = Order.SERVED
        order.save(update_fields=['status', 'updated_at'])

    return redirect('staffops:serveur_table_detail', table_id=order.table.id)


@login_required
@role_required(Role.SERVEUR, Role.MANAGER)
def serveur_request_bill(request, order_id):
    order = get_object_or_404(Order, id=order_id, mode=Order.ONSITE)

    if order.status == Order.SERVED:
        order.status = Order.BILL_REQUESTED
        order.save(update_fields=['status', 'updated_at'])

    return redirect('staffops:serveur_table_detail', table_id=order.table.id)






@login_required
@role_required(Role.MANAGER, Role.CHEF, Role.SERVEUR, Role.CAISSIER, Role.MENAGE, Role.LIVREUR)
def staff_profile(request):
    return render(request, 'staff/profile.html', {
        'active_page': 'profile',
    })

@login_required
@role_required(Role.LIVREUR, Role.MANAGER)
def livreur(request):
    orders = Order.objects.filter(
        mode=Order.DELIVERY,
        status__in=[Order.READY, Order.OUT_FOR_DELIVERY]
    ).prefetch_related('items__dish').order_by('-updated_at')

    return render(request, 'staff/livreur.html', {
        'orders': orders,
        'active_page': 'livreur',
    })


@login_required
@role_required(Role.LIVREUR, Role.MANAGER)
def update_delivery_status(request, pk, status):
    order = get_object_or_404(
        Order,
        pk=pk,
        mode=Order.DELIVERY,
        status__in=[
            Order.READY,
            Order.OUT_FOR_DELIVERY,
        ]
    )

    allowed_statuses = [
        Order.OUT_FOR_DELIVERY,
        Order.DELIVERED,
    ]

    if status in allowed_statuses:
        order.status = status
        order.save(update_fields=['status', 'updated_at'])

    return redirect('staffops:livreur')



@login_required
@role_required(Role.CAISSIER, Role.MANAGER)
def commandes_history(request):
    from decimal import Decimal

    # Filtres
    date_str   = request.GET.get('date', '')
    status_filter = request.GET.get('status', '')
    mode_filter   = request.GET.get('mode', '')

    qs = Order.objects.prefetch_related('items__dish').select_related('table', 'user').order_by('-created_at')

    if date_str:
        try:
            from datetime import date as ddate
            d = ddate.fromisoformat(date_str)
            qs = qs.filter(created_at__date=d)
        except ValueError:
            pass
    if status_filter:
        qs = qs.filter(status=status_filter)
    if mode_filter:
        qs = qs.filter(mode=mode_filter)

    orders_list = list(qs)
    ca_total    = sum(o.total for o in orders_list)
    paid_count  = sum(1 for o in orders_list if o.status == Order.PAID)

    return render(request, 'staff/commandes_history.html', {
        'orders': orders_list,
        'ca_total': ca_total,
        'total_count': len(orders_list),
        'paid_count': paid_count,
        'statuses': Order.STATUS,
        'modes': Order.MODES,
        'current_date': date_str,
        'current_status': status_filter,
        'current_mode': mode_filter,
        'active_page': 'commandes_history',
    })


@login_required
@role_required(Role.MANAGER, Role.CHEF, Role.SERVEUR, Role.CAISSIER, Role.MENAGE, Role.LIVREUR)
def staff_payments(request):
    payments = StaffPayment.objects.filter(employee=request.user).select_related('paid_by')

    return render(request, 'staff/payments.html', {
        'payments': payments,
        'active_page': 'payments',
    })
