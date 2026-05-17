from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from menu.models import Dish
from .models import Order, OrderItem

def cart_view(request):
    return render(request, "orders/cart.html")


@login_required
def cart_add(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id, is_active=True, manual_available=True)
    if request.method != "POST":
        return redirect("menu:detail", slug=dish.slug)

    cart = request.session.get("cart", {})
    dish_id = str(dish.id)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    quantity = max(1, quantity)

    cart[dish_id] = cart.get(dish_id, 0) + quantity

    request.session["cart"] = cart
    request.session.modified = True
    messages.success(request, f"{dish.name} a ete ajoute au panier.")

    return redirect("orders:cart")


def cart_remove(request, dish_id):
    cart = request.session.get("cart", {})
    dish_id = str(dish_id)

    if dish_id in cart:
        del cart[dish_id]

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("orders:cart")


def cart_increase(request, dish_id):
    cart = request.session.get("cart", {})
    dish_id = str(dish_id)

    if dish_id in cart:
        cart[dish_id] += 1

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("orders:cart")


def cart_decrease(request, dish_id):
    cart = request.session.get("cart", {})
    dish_id = str(dish_id)

    if dish_id in cart:
        cart[dish_id] -= 1
        if cart[dish_id] <= 0:
            del cart[dish_id]

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("orders:cart")


@login_required
def checkout(request):
    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Votre panier est vide.")
        return redirect("menu:list")

    if request.method == "POST":
        address = request.POST.get("address", "")

        if not address:
            messages.error(request, "Veuillez saisir votre adresse de livraison.")
            return redirect("orders:checkout")

        order = Order.objects.create(
            user=request.user,
            table=None,
            mode=Order.DELIVERY,
            status=Order.PENDING,
            customer_name=f"{request.POST.get('first_name', '')} {request.POST.get('last_name', '')}",
            phone=request.POST.get("phone", ""),
            delivery_address=address,
            notes=request.POST.get("notes", ""),
        )

        for dish_id, quantity in cart.items():
            dish = get_object_or_404(Dish, id=dish_id)

            OrderItem.objects.create(
                order=order,
                dish=dish,
                dish_name=dish.name,
                quantity=int(quantity),
                unit_price=dish.price,
            )

        request.session["cart"] = {}
        request.session.modified = True

        messages.success(request, "Votre commande en livraison a été créée avec succès.")
        return redirect("orders:my_orders")

    return render(request, "orders/checkout.html")

@login_required
def my_orders_view(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items__dish").order_by("-created_at")

    return render(request, "accounts/my_orders.html", {
        "orders": orders,
    })
