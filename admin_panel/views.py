import json
import datetime
from django.shortcuts import get_object_or_404, redirect,render
from django.contrib import messages
from django.db import models,transaction
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDate
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from accounts.decorators import role_required,login_required
from accounts.models import Role, User
from audit.models import AuditLog
from menu.models import Category, Dish,DishIngredient
from orders.models import Order, OrderItem
from reservations.models import Reservation
from stock.models import Ingredient, IngredientCategory

from .forms import DishForm, StaffCreateForm, StaffUpdateForm,StaffPaymentForm,IngredientForm,RestaurantSettingsForm, CategoryForm, IngredientCategoryForm
from staffops.models import StaffPayment

from .models import ActivityLog,RestaurantSettings
from admin_panel.utils import create_log

from tables.models import RestaurantTable, TableStatus
from tables.forms import RestaurantTableForm
from tables.models import TableZone

from reservations.models import Reservation, ReservationStatus
from reservations.forms import AdminReservationForm

from decimal import Decimal


def _infer_table_zone(pos_x, pos_y):
    if pos_y < 55:
        if pos_x >= 72:
            return TableZone.VIP
        return TableZone.INTERIEUR

    if pos_x < 45:
        return TableZone.TERRASSE

    if pos_x < 75:
        return TableZone.FAMILLE

    return TableZone.BAR

@role_required(Role.ADMIN)
def home(request):
    today = timezone.now().date()
    seven_days_ago = today - datetime.timedelta(days=6)

    # Revenue per day (Order.total is a property — aggregate via OrderItem)
    rev_qs = (
        OrderItem.objects
        .filter(order__status=Order.PAID, order__created_at__date__gte=seven_days_ago)
        .annotate(day=TruncDate('order__created_at'))
        .values('day')
        .annotate(rev=Sum(F('quantity') * F('unit_price')))
        .order_by('day')
    )
    rev_dict = {r['day']: float(r['rev'] or 0) for r in rev_qs}
    revenue_labels, revenue_data = [], []
    for i in range(7):
        d = seven_days_ago + datetime.timedelta(days=i)
        revenue_labels.append(d.strftime('%d %b'))
        revenue_data.append(rev_dict.get(d, 0))

    kpi_revenue_today = float(
        OrderItem.objects
        .filter(order__status=Order.PAID, order__created_at__date=today)
        .aggregate(rev=Sum(F('quantity') * F('unit_price')))['rev'] or 0
    )

    # Orders by status
    status_labels = dict(Order.STATUS)
    orders_by_status = [
        {'label': status_labels.get(r['status'], r['status']), 'count': r['count']}
        for r in Order.objects.values('status').annotate(count=Count('id'))
    ]

    # Orders by mode
    mode_labels = dict(Order.MODES)
    orders_by_mode = [
        {'label': mode_labels.get(r['mode'], r['mode']), 'count': r['count']}
        for r in Order.objects.values('mode').annotate(count=Count('id'))
    ]

    # Top 5 dishes by quantity ordered
    top_dishes = [
        {'label': r['dish_name'] or 'Inconnu', 'qty': r['qty']}
        for r in (
            OrderItem.objects
            .values('dish_name')
            .annotate(qty=Sum('quantity'))
            .order_by('-qty')[:5]
        )
    ]

    # Reservations by status
    res_labels = dict(ReservationStatus.choices)
    res_by_status = [
        {'label': res_labels.get(r['status'], r['status']), 'count': r['count']}
        for r in Reservation.objects.values('status').annotate(count=Count('id'))
    ]

    # Users by role
    role_map = {r.value: r.label for r in Role}
    users_by_role = [
        {'label': role_map.get(r['role'], r['role']), 'count': r['count']}
        for r in User.objects.values('role').annotate(count=Count('id'))
    ]

    # Tables by status
    tbl_map = {s.value: s.label for s in TableStatus}
    tables_by_status = [
        {'label': tbl_map.get(r['status'], r['status']), 'count': r['count']}
        for r in RestaurantTable.objects.values('status').annotate(count=Count('id'))
    ]

    return render(request, 'admin_panel/home.html', {
        'active_page': 'home',
        # KPIs
        'kpi_orders_today': Order.objects.filter(created_at__date=today).count(),
        'kpi_revenue_today': round(kpi_revenue_today, 2),
        'kpi_reservations': Reservation.objects.count(),
        'kpi_users': User.objects.count(),
        'kpi_low_stock': Ingredient.objects.filter(quantity__lte=models.F('alert_threshold')).count(),
        'kpi_tables_avail': RestaurantTable.objects.filter(status=TableStatus.AVAILABLE).count(),
        'kpi_orders_total': Order.objects.count(),
        # Chart JSON
        'chart_revenue_labels': json.dumps(revenue_labels),
        'chart_revenue_data': json.dumps(revenue_data),
        'chart_orders_status': json.dumps(orders_by_status),
        'chart_orders_mode': json.dumps(orders_by_mode),
        'chart_top_dishes': json.dumps(top_dishes),
        'chart_res_status': json.dumps(res_by_status),
        'chart_users_role': json.dumps(users_by_role),
        'chart_tables_status': json.dumps(tables_by_status),
        # Lists
        'recent_orders': Order.objects.select_related('user').prefetch_related('items')[:8],
        'low_stock_items': Ingredient.objects.filter(quantity__lte=models.F('alert_threshold'))[:6],
        'logs': AuditLog.objects.select_related('user')[:12],
    })

@role_required(Role.ADMIN)
def admin_profile(request):
    return render(
        request,
        "admin_panel/admin_profile.html"
    )

@role_required(Role.ADMIN)
def menu_admin(request):
    selected_category = request.GET.get("category", "")
    search = request.GET.get("q", "").strip()

    dishes = Dish.objects.select_related("category").prefetch_related(
        "composition__ingredient"
    ).all()

    categories = Category.objects.all()
    ingredients = Ingredient.objects.all()
    form = DishForm()

    if selected_category:
        dishes = dishes.filter(category_id=selected_category)

    if search:
        dishes = dishes.filter(
            models.Q(name__icontains=search) |
            models.Q(description__icontains=search) |
            models.Q(category__name__icontains=search)
        )

    return render(request, "admin_panel/menu_admin.html", {
        "active_page": "menu",
        "dishes": dishes,
        "categories": categories,
        "ingredients": ingredients,
        "form": form,
        "selected_category": selected_category,
        "search": search,
    })


@role_required(Role.ADMIN)
def categories(request):
    categories_list = Category.objects.all()
    form = CategoryForm()

    q = request.GET.get("q")

    if q:
        categories_list = categories_list.filter(name__icontains=q)

    return render(request, "admin_panel/categories.html", {
        "active_page": "categories",
        "categories": categories_list,
        "form": form,
    })


@role_required(Role.ADMIN)
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            category = form.save()

            create_log(
                request,
                "create",
                "Catégories",
                f"A ajouté la catégorie {category.name}",
                category.id
            )

            messages.success(request, "Catégorie ajoutée avec succès.")
        else:
            messages.error(request, "Erreur lors de l’ajout de la catégorie.")

    return redirect("admin_panel:categories")


@role_required(Role.ADMIN)
def category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)

        if form.is_valid():
            form.save()

            create_log(
                request,
                "update",
                "Catégories",
                f"A modifié la catégorie {category.name}",
                category.id
            )

            messages.success(request, "Catégorie modifiée avec succès.")
        else:
            messages.error(request, "Erreur lors de la modification.")

    return redirect("admin_panel:categories")


@role_required(Role.ADMIN)
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        if category.dishes.exists():
            category.is_active = False
            category.save(update_fields=["is_active"])

            create_log(
                request,
                "delete",
                "Catégories",
                f"A désactivé la catégorie {category.name}",
                category.id
            )

            messages.warning(
                request,
                "La catégorie contient des plats, elle a été désactivée au lieu d’être supprimée."
            )
        else:
            name = category.name
            category.delete()

            create_log(
                request,
                "delete",
                "Catégories",
                f"A supprimé la catégorie {name}",
                category_id
            )

            messages.success(request, "Catégorie supprimée avec succès.")

    return redirect("admin_panel:categories")

@role_required(Role.ADMIN)
def dish_create(request):
    if request.method == "POST":
        form = DishForm(request.POST, request.FILES)

        ingredient_ids = request.POST.getlist("ingredient_id[]")
        quantities = request.POST.getlist("quantity[]")
        units = request.POST.getlist("unit[]")

        if form.is_valid():
            dish = form.save()

            for ingredient_id, quantity, unit in zip(ingredient_ids, quantities, units):
                if ingredient_id and quantity and unit:
                    DishIngredient.objects.create(
                        dish=dish,
                        ingredient_id=ingredient_id,
                        quantity=quantity,
                        unit=unit
                    )

            create_log(
                request,
                "create",
                "Menu",
                f"A ajouté le plat {dish.name} avec sa composition",
                dish.id
            )

            messages.success(request, "Plat ajouté avec succès.")
        else:
            messages.error(request, "Erreur lors de l'ajout du plat.")

    return redirect("admin_panel:menu_admin")


@role_required(Role.ADMIN)
def dish_update(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)

    if request.method == "POST":
        form = DishForm(request.POST, request.FILES, instance=dish)

        ingredient_ids = request.POST.getlist("ingredient_id[]")
        quantities = request.POST.getlist("quantity[]")
        units = request.POST.getlist("unit[]")

        if form.is_valid():
            dish = form.save()

            dish.composition.all().delete()

            for ingredient_id, quantity, unit in zip(ingredient_ids, quantities, units):
                if ingredient_id and quantity and unit:
                    DishIngredient.objects.create(
                        dish=dish,
                        ingredient_id=ingredient_id,
                        quantity=quantity,
                        unit=unit
                    )

            create_log(
                request,
                "update",
                "Menu",
                f"A modifié le plat {dish.name} et sa composition",
                dish.id
            )

            messages.success(request, "Plat modifié avec succès.")
        else:
            messages.error(request, "Erreur lors de la modification.")

    return redirect("admin_panel:menu_admin")

@role_required(Role.ADMIN)
def dish_delete(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)

    if request.method == 'POST':
        active_order_statuses = [
            Order.PENDING,
            Order.PREPARING,
            Order.COOKING,
            Order.READY,
            Order.SERVED,
            Order.OUT_FOR_DELIVERY,
            Order.BILL_REQUESTED,
        ]

        if dish.orderitem_set.filter(order__status__in=active_order_statuses).exists():
            dish.is_active = False
            dish.manual_available = False
            dish.save(update_fields=["is_active", "manual_available"])

            create_log(
                request,
                "delete",
                "Menu",
                f"A desactive le plat {dish.name} car il est lie a des commandes en cours",
                dish.id
            )

            messages.warning(
                request,
                "Ce plat est lié à des commandes en cours. Il a été désactivé au lieu d'être supprimé."
            )
            return redirect('admin_panel:menu_admin')

        dish_name = dish.name
        dish.delete()

        create_log(
            request,
            "delete",
            "Menu",
            f"A supprime le plat {dish_name}",
            dish_id
        )

        messages.success(request, "Plat supprime avec succes.")

    return redirect('admin_panel:menu_admin')


from orders.models import Order, OrderItem
from tables.models import TableStatus
from admin_panel.utils import create_log


@role_required(Role.ADMIN)
def orders(request):
    orders_list = Order.objects.select_related(
        "user", "table"
    ).prefetch_related(
        "items__dish"
    ).order_by("-created_at")

    status = request.GET.get("status")
    mode = request.GET.get("mode")
    q = request.GET.get("q")

    if status:
        orders_list = orders_list.filter(status=status)

    if mode:
        orders_list = orders_list.filter(mode=mode)

    if q:
        orders_list = orders_list.filter(customer_name__icontains=q)

    return render(request, "admin_panel/orders.html", {
        "active_page": "orders",
        "orders": orders_list,
        "statuses": Order.STATUS,
        "modes": Order.MODES,
        "selected_mode": mode,
        "selected_status": status,
    })

@role_required(Role.ADMIN)
def order_update_status(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__dish__composition__ingredient"
        ),
        id=order_id
    )

    if request.method == "POST":
        old_status = order.status
        new_status = request.POST.get("status")

        with transaction.atomic():
            order.status = new_status
            order.save(update_fields=["status"])

            # 1. Diminuer le stock seulement au passage vers PREPARING
            if old_status != Order.PREPARING and new_status == Order.PREPARING:
                for item in order.items.all():
                    for comp in item.dish.composition.all():
                        ingredient = comp.ingredient
                        quantity_to_remove = comp.quantity * item.quantity

                        if ingredient.quantity < quantity_to_remove:
                            messages.error(
                                request,
                                f"Stock insuffisant pour {ingredient.name}."
                            )
                            return redirect("admin_panel:orders")

                        ingredient.quantity -= quantity_to_remove
                        ingredient.save(update_fields=["quantity"])

                create_log(
                    request,
                    "stock",
                    "Stock",
                    f"Stock diminué automatiquement pour la commande #{order.id}",
                    order.id
                )

            # 2. Gestion des tables si un jour commande sur place
            if order.table:
                if new_status in [
                    Order.PENDING,
                    Order.PREPARING,
                    Order.COOKING,
                    Order.READY,
                    Order.SERVED,
                ]:
                    order.table.status = TableStatus.OCCUPIED

                elif new_status == Order.CANCELLED:
                    order.table.status = TableStatus.AVAILABLE

                order.table.save(update_fields=["status"])

            # 3. Log changement statut
            create_log(
                request,
                "update",
                "Commandes",
                f"Commande #{order.id} : {old_status} → {new_status}",
                order.id
            )

        messages.success(request, "Statut de la commande mis à jour.")

    return redirect("admin_panel:orders")

@role_required(Role.ADMIN)
def order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        if order.table:
            order.table.status = TableStatus.AVAILABLE
            order.table.save(update_fields=["status"])

        order.delete()

        create_log(
            request,
            "delete",
            "Commandes",
            f"A supprimé la commande #{order_id}",
            order_id
        )

        messages.success(request, "Commande supprimée avec succès.")

    return redirect("admin_panel:orders")

@role_required(Role.ADMIN)
def order_update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        old_status = order.status
        new_status = request.POST.get("status")

        order.status = new_status
        order.save(update_fields=["status"])

        if order.table:
            if new_status in ["pending", "preparing", "ready", "served"]:
                order.table.status = TableStatus.OCCUPIED
            elif new_status == "paid":
                order.table.status = TableStatus.NEEDS_CLEANING
            elif new_status == "cancelled":
                order.table.status = TableStatus.AVAILABLE

            order.table.save(update_fields=["status"])

        create_log(
            request,
            "update",
            "Commandes",
            f"Commande #{order.id} : {old_status} → {new_status}",
            order.id
        )

        messages.success(request, "Statut de la commande mis à jour.")

    return redirect("admin_panel:orders")


@role_required(Role.ADMIN)
def order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        if order.table:
            order.table.status = TableStatus.AVAILABLE
            order.table.save(update_fields=["status"])

        order.delete()

        create_log(
            request,
            "delete",
            "Commandes",
            f"A supprimé la commande #{order_id}",
            order_id
        )

        messages.success(request, "Commande supprimée avec succès.")

    return redirect("admin_panel:orders")


@role_required(Role.ADMIN)
def reservations(request):
    reservations_list = Reservation.objects.select_related("user", "table").all()

    q = request.GET.get("q")
    status = request.GET.get("status")

    if q:
        reservations_list = reservations_list.filter(full_name__icontains=q)

    if status:
        reservations_list = reservations_list.filter(status=status)

    form = AdminReservationForm()

    return render(request, "admin_panel/reservations.html", {
        "active_page": "reservations",
        "reservations": reservations_list,
        "form": form,
        "statuses": ReservationStatus.choices,
        "selected_status": status,
    })


@role_required(Role.ADMIN)
def reservation_create(request):
    if request.method == "POST":
        form = AdminReservationForm(request.POST)

        if form.is_valid():
            reservation = form.save()

            if reservation.table and reservation.status in ["pending", "confirmed"]:
                reservation.table.status = TableStatus.RESERVED
                reservation.table.save(update_fields=["status"])

            create_log(
                request,
                "create",
                "Réservations",
                f"A créé une réservation pour {reservation.full_name}",
                reservation.id
            )

            messages.success(request, "Réservation créée avec succès.")
        else:
            messages.error(request, "Erreur lors de la création.")

    return redirect("admin_panel:reservations")


@role_required(Role.ADMIN)
def reservation_update(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    old_table = reservation.table
    old_status = reservation.status

    if request.method == "POST":
        form = AdminReservationForm(request.POST, instance=reservation)

        if form.is_valid():
            reservation = form.save()

            if old_table and old_table != reservation.table:
                old_table.status = TableStatus.AVAILABLE
                old_table.save(update_fields=["status"])

            if reservation.table:
                if reservation.status in ["pending", "confirmed"]:
                    reservation.table.status = TableStatus.RESERVED
                elif reservation.status == "seated":
                    reservation.table.status = TableStatus.OCCUPIED
                elif reservation.status in ["done", "cancelled"]:
                    reservation.table.status = TableStatus.AVAILABLE

                reservation.table.save(update_fields=["status"])

            create_log(
                request,
                "update",
                "Réservations",
                f"Réservation {reservation.full_name} modifiée : {old_status} → {reservation.status}",
                reservation.id
            )

            messages.success(request, "Réservation modifiée avec succès.")
        else:
            messages.error(request, "Erreur lors de la modification.")

    return redirect("admin_panel:reservations")


@role_required(Role.ADMIN)
def reservation_delete(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.method == "POST":
        if reservation.table:
            reservation.table.status = TableStatus.AVAILABLE
            reservation.table.save(update_fields=["status"])

        name = reservation.full_name
        reservation.delete()

        create_log(
            request,
            "delete",
            "Réservations",
            f"A supprimé la réservation de {name}",
            reservation_id
        )

        messages.success(request, "Réservation supprimée avec succès.")

    return redirect("admin_panel:reservations")


@role_required(Role.ADMIN)
def reservation_confirm(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.method == "POST":
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save(update_fields=["status"])

        if reservation.table:
            reservation.table.status = TableStatus.RESERVED
            reservation.table.save(update_fields=["status"])

        if reservation.email:
            from django.conf import settings
            send_mail(
                "Réservation confirmée",
                "Votre réservation est confirmée. Nous vous attendons avec plaisir.",
                settings.DEFAULT_FROM_EMAIL,
                [reservation.email],
                fail_silently=True,
            )

        messages.success(request, "Réservation confirmée.")

    return redirect("admin_panel:reservations")


@role_required(Role.ADMIN)
def reservation_mark_seated(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.method == "POST":
        reservation.status = ReservationStatus.SEATED
        reservation.save(update_fields=["status"])

        if reservation.table:
            reservation.table.status = TableStatus.OCCUPIED
            reservation.table.save(update_fields=["status"])

        messages.success(request, "Client installé à table.")

    return redirect("admin_panel:reservations")


@role_required(Role.ADMIN)
def reservation_mark_done(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.method == "POST":
        reservation.status = ReservationStatus.DONE
        reservation.save(update_fields=["status"])

        if reservation.table:
            reservation.table.status = TableStatus.NEEDS_CLEANING
            reservation.table.save(update_fields=["status"])

        messages.success(request, "Réservation terminée. Table envoyée au nettoyage.")

    return redirect("admin_panel:reservations")




@role_required(Role.ADMIN,Role.MANAGER)
def staff(request):
    if request.user.role == Role.MANAGER:
        staff_users = User.objects.exclude(
            role__in=[Role.CLIENT, Role.ADMIN, Role.MANAGER])
    else:
        staff_users = User.objects.exclude(role=Role.CLIENT).exclude(role=Role.ADMIN)

    create_form = StaffCreateForm()
    update_form = StaffUpdateForm()
    payment_form = StaffPaymentForm()

    return render(request, 'admin_panel/staff.html', {
        'active_page': 'staff',
        'staff_users': staff_users,
        'create_form': create_form,
        'update_form': update_form,
        'payment_form': payment_form,
    })


@role_required(Role.ADMIN)
def staff_create(request):
    if request.method == 'POST':
        form = StaffCreateForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Employé ajouté avec succès.")
        else:
            messages.error(request, form.errors)

    return redirect('admin_panel:staff')


@role_required(Role.ADMIN)
def staff_update(request, user_id):
    employee = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = StaffUpdateForm(request.POST, instance=employee)

        if form.is_valid():
            form.save()
            messages.success(request, "Employé modifié avec succès.")
        else:
            messages.error(request, "Erreur lors de la modification.")

    return redirect('admin_panel:staff')


@role_required(Role.ADMIN)
def staff_delete(request, user_id):
    employee = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        employee.is_active = False
        employee.save(update_fields=['is_active'])
        messages.success(request, "Employé désactivé avec succès.")

    return redirect('admin_panel:staff')


@role_required(Role.ADMIN,Role.MANAGER)
def staff_payment_create(request, user_id):
    employee = get_object_or_404(User, id=user_id)

    if request.user.role == Role.MANAGER and employee.role in [Role.ADMIN, Role.MANAGER]:
        messages.error(request, "Le manager ne peut pas payer un admin ou un autre manager.")
        return redirect('admin_panel:staff')
    
    if request.method == 'POST':
        form = StaffPaymentForm(request.POST)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.employee = employee
            payment.paid_by = request.user
            payment.save()
            messages.success(request, "Paiement enregistré avec succès.")
        else:
            messages.error(request, "Erreur lors du paiement.")

    return redirect('admin_panel:staff')


@role_required(Role.ADMIN, Role.MANAGER)
def staff_payment_history(request, user_id):
    employee = get_object_or_404(User, id=user_id)

    if request.user.role == Role.MANAGER and employee.role in [Role.ADMIN, Role.MANAGER]:
        messages.error(request, "Accès non autorisé.")
        return redirect('admin_panel:staff')

    payments = StaffPayment.objects.filter(employee=employee)

    return render(request, 'admin_panel/staff_payment_history.html', {
        'active_page': 'staff',
        'employee': employee,
        'payments': payments,
    })


@role_required(Role.ADMIN)
def stock(request):
    selected_category = request.GET.get("category", "")
    ingredients = Ingredient.objects.select_related("category").all()
    form = IngredientForm()
    category_form = IngredientCategoryForm()
    stock_categories = IngredientCategory.objects.prefetch_related("ingredients").all()
    low_stock_items = Ingredient.objects.filter(
        quantity__lte=models.F('alert_threshold')
    )

    if selected_category == "uncategorized":
        ingredients = ingredients.filter(category__isnull=True)
    elif selected_category:
        ingredients = ingredients.filter(category_id=selected_category)

    if selected_category:
        if selected_category == "uncategorized":
            low_stock_items = low_stock_items.filter(category__isnull=True)
        else:
            low_stock_items = low_stock_items.filter(category_id=selected_category)

    return render(request, 'admin_panel/stock.html', {
        'active_page': 'stock',
        'ingredients': ingredients,
        'form': form,
        'category_form': category_form,
        'stock_categories': stock_categories,
        'low_stock_items': low_stock_items,
        'selected_category': selected_category,
    })



@role_required(Role.ADMIN)
def ingredient_create(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Ingrédient ajouté avec succès.")
        else:
            messages.error(request, "Erreur lors de l'ajout de l'ingrédient.")

    return redirect('admin_panel:stock')


@role_required(Role.ADMIN)
def ingredient_category_create(request):
    if request.method == 'POST':
        form = IngredientCategoryForm(request.POST)

        if form.is_valid():
            category = form.save()
            create_log(request, "create", "Stock", f"A ajouté la catégorie de stock {category.name}", category.id)
            messages.success(request, "Catégorie de stock ajoutée avec succès.")
        else:
            messages.error(request, "Erreur lors de l'ajout de la catégorie de stock.")

    return redirect('admin_panel:stock')


@role_required(Role.ADMIN)
def ingredient_category_update(request, category_id):
    category = get_object_or_404(IngredientCategory, id=category_id)

    if request.method == 'POST':
        form = IngredientCategoryForm(request.POST, instance=category)

        if form.is_valid():
            form.save()
            create_log(request, "update", "Stock", f"A modifié la catégorie de stock {category.name}", category.id)
            messages.success(request, "Catégorie de stock modifiée avec succès.")
        else:
            messages.error(request, "Erreur lors de la modification de la catégorie de stock.")

    return redirect('admin_panel:stock')


@role_required(Role.ADMIN)
def ingredient_category_delete(request, category_id):
    category = get_object_or_404(IngredientCategory, id=category_id)

    if request.method == 'POST':
        if category.ingredients.exists():
            category.is_active = False
            category.save(update_fields=["is_active"])
            create_log(request, "delete", "Stock", f"A désactivé la catégorie de stock {category.name}", category.id)
            messages.warning(request, "Cette catégorie contient encore des ingrédients. Elle a été désactivée au lieu d'être supprimée.")
        else:
            category_name = category.name
            category.delete()
            create_log(request, "delete", "Stock", f"A supprimé la catégorie de stock {category_name}", category_id)
            messages.success(request, "Catégorie de stock supprimée avec succès.")

    return redirect('admin_panel:stock')


@role_required(Role.ADMIN)
def ingredient_update(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)

        if form.is_valid():
            form.save()
            messages.success(request, "Stock modifié avec succès.")
        else:
            messages.error(request, "Erreur lors de la modification.")

    return redirect('admin_panel:stock')


@role_required(Role.ADMIN)
def ingredient_delete(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    if request.method == 'POST':
        ingredient.delete()
        messages.success(request, "Ingrédient supprimé avec succès.")

    return redirect('admin_panel:stock')



# @role_required(Role.ADMIN)
# def logs(request):
#     logs_list = AuditLog.objects.select_related('user')[:100]

#     return render(request, 'admin_panel/logs.html', {
#         'active_page': 'logs',
#         'logs': logs_list,
#     })

@login_required
def logs_view(request):
    logs = ActivityLog.objects.select_related("user").all()

    action_type = request.GET.get("type")
    module = request.GET.get("module")
    search = request.GET.get("q")

    if action_type:
        logs = logs.filter(action_type=action_type)

    if module:
        logs = logs.filter(module__icontains=module)

    if search:
        logs = logs.filter(description__icontains=search)

    context = {
        "logs": logs[:200],
        "selected_type": action_type,
        "selected_module": module,
        "search": search,
    }

    return render(request, "admin_panel/logs.html", context)


@role_required(Role.ADMIN)
def settings_view(request):
    settings_obj, created = RestaurantSettings.objects.get_or_create(id=1)

    if request.method == "POST":
        form = RestaurantSettingsForm(request.POST, instance=settings_obj)

        if form.is_valid():
            form.save()

            create_log(
                request,
                action_type="update",
                module="Paramètres",
                description="A modifié les paramètres système",
                object_id=settings_obj.id
            )

            messages.success(request, "Paramètres enregistrés avec succès.")
            return redirect("admin_panel:settings")
        else:
            messages.error(request, "Erreur lors de l’enregistrement des paramètres.")
    else:
        form = RestaurantSettingsForm(instance=settings_obj)

    return render(request, "admin_panel/settings.html", {
        "active_page": "settings",
        "form": form,
        "settings_obj": settings_obj,
    })



@role_required(Role.ADMIN)
def tables(request):
    zone = request.GET.get("zone")
    status = request.GET.get("status")
    q = request.GET.get("q")
    sort = request.GET.get("sort", "number")
    direction = request.GET.get("dir", "asc")

    allowed_sorts = {
        "name": "name",
        "number": "number",
        "zone": "zone",
        "capacity": "capacity",
        "status": "status",
        "position": "pos_x",
        "active": "is_active",
    }

    if sort not in allowed_sorts:
        sort = "number"

    if direction not in {"asc", "desc"}:
        direction = "asc"

    tables_list = RestaurantTable.objects.all()

    if zone:
        tables_list = tables_list.filter(zone=zone)

    if status:
        tables_list = tables_list.filter(status=status)

    if q:
        tables_list = tables_list.filter(name__icontains=q)

    order_field = allowed_sorts[sort]
    if direction == "desc":
        order_field = f"-{order_field}"
    tables_list = tables_list.order_by(order_field, "number")

    form = RestaurantTableForm()

    context = {
        "active_page": "tables",
        "tables": tables_list,
        "form": form,
        "zones": RestaurantTable._meta.get_field("zone").choices,
        "statuses": RestaurantTable._meta.get_field("status").choices,
        "selected_zone": zone,
        "selected_status": status,
        "q": q,
        "sort": sort,
        "direction": direction,
        "total_tables": tables_list.count(),
        "available_count": RestaurantTable.objects.filter(status=TableStatus.AVAILABLE).count(),
        "occupied_count": RestaurantTable.objects.filter(status=TableStatus.OCCUPIED).count(),
        "reserved_count": RestaurantTable.objects.filter(status=TableStatus.RESERVED).count(),
        "cleaning_count": RestaurantTable.objects.filter(status=TableStatus.NEEDS_CLEANING).count(),
    }

    return render(request, "admin_panel/table.html", context)


@role_required(Role.ADMIN)
def table_create(request):
    if request.method == "POST":
        form = RestaurantTableForm(request.POST)

        if form.is_valid():
            table = form.save(commit=False)
            table.zone = _infer_table_zone(table.pos_x, table.pos_y)
            table.save()

            create_log(
                request,
                "create",
                "Tables",
                f"A ajouté la table {table.name}",
                table.id
            )

            messages.success(request, "Table ajoutée avec succès.")
        else:
            messages.error(request, "Erreur lors de l’ajout de la table.")

    return redirect("admin_panel:tables")


@role_required(Role.ADMIN)
def table_update(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)

    if request.method == "POST":
        form = RestaurantTableForm(request.POST, instance=table)

        if form.is_valid():
            table = form.save(commit=False)
            table.zone = _infer_table_zone(table.pos_x, table.pos_y)
            table.save()

            create_log(
                request,
                "update",
                "Tables",
                f"A modifié la table {table.name}",
                table.id
            )

            messages.success(request, "Table modifiée avec succès.")
        else:
            messages.error(request, "Erreur lors de la modification.")

    return redirect("admin_panel:tables")


@role_required(Role.ADMIN)
def table_delete(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)

    if request.method == "POST":
        table.is_active = False
        table.status = TableStatus.OUT_OF_SERVICE
        table.save(update_fields=["is_active", "status"])

        create_log(
            request,
            "delete",
            "Tables",
            f"A désactivé la table {table.name}",
            table.id
        )

        messages.success(request, "Table désactivée avec succès.")

    return redirect("admin_panel:tables")


@role_required(Role.ADMIN)
def table_change_status(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)

    if request.method == "POST":
        old_status = table.get_status_display()
        table.status = request.POST.get("status")
        table.save(update_fields=["status"])

        create_log(
            request,
            "table",
            "Tables",
            f"Table {table.name} : {old_status} → {table.get_status_display()}",
            table.id
        )

        messages.success(request, "Statut de la table mis à jour.")

    return redirect("admin_panel:tables")


@role_required(Role.ADMIN)
def table_reposition(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)

    try:
        pos_x = round(float(request.POST.get("pos_x", table.pos_x)))
        pos_y = round(float(request.POST.get("pos_y", table.pos_y)))
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "error": "Invalid coordinates"}, status=400)

    pos_x = max(0, min(pos_x, 100))
    pos_y = max(0, min(pos_y, 100))
    new_zone = _infer_table_zone(pos_x, pos_y)

    table.pos_x = pos_x
    table.pos_y = pos_y
    table.zone = new_zone
    table.save(update_fields=["pos_x", "pos_y", "zone", "updated_at"])

    return JsonResponse({
        "success": True,
        "pos_x": pos_x,
        "pos_y": pos_y,
        "zone": table.zone,
        "zone_label": table.get_zone_display(),
    })
