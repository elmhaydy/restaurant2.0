from django.db.models import Prefetch
from django.shortcuts import get_object_or_404,redirect,render
from admin_panel.utils import create_log

from .models import Category, Dish
from orders.models import Order

def menu_list(request):
    available_dishes = Dish.objects.filter(
        is_active=True,
        manual_available=True
    ).select_related('category')

    categories = Category.objects.filter(
        is_active=True,
        dishes__is_active=True,
        dishes__manual_available=True,
    ).distinct().prefetch_related(
        Prefetch('dishes', queryset=available_dishes)
    )

    return render(request, 'public/menu.html', {
        'categories': categories,
        'dishes': available_dishes,
    })


def dish_detail(request, slug):
    dish = get_object_or_404(
        Dish.objects
            .select_related('category')
            .prefetch_related('composition__ingredient'),
        slug=slug,
        is_active=True,
        manual_available=True,
    )

    return render(request, 'public/detail.html', {
        'dish': dish,
    })

def delete_menu_item(request, item_id):
    item = get_object_or_404(Dish, id=item_id)
    item_name = item.name
    item.delete()

    create_log(
        request,
        action_type="delete",
        module="Menu",
        description=f"A supprimé le plat : {item_name}",
        object_id=item_id
    )

    return redirect("menu_list")


def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get("status")

    old_status = order.status
    order.status = new_status
    order.save()

    create_log(
        request,
        action_type="order",
        module="Commandes",
        description=f"Commande #{order.id} passée de {old_status} à {new_status}",
        object_id=order.id
    )

    return redirect("orders_list")
