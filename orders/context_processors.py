from decimal import Decimal
from menu.models import Dish

def cart_context(request):
    cart = request.session.get("cart", {})

    cart_items = []
    cart_count = 0
    cart_total = Decimal("0.00")

    for dish_id, quantity in cart.items():
        try:
            dish = Dish.objects.get(id=dish_id)
            quantity = int(quantity)
            subtotal = dish.price * quantity

            cart_items.append({
                "dish": dish,
                "quantity": quantity,
                "subtotal": subtotal,
            })

            cart_count += quantity
            cart_total += subtotal
        except Dish.DoesNotExist:
            continue

    return {
        "cart_items": cart_items,
        "cart_count": cart_count,
        "cart_total": cart_total,
    }