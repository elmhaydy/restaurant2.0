from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.decorators import role_required
from accounts.models import Role
from admin_panel.utils import create_log

from .models import RestaurantTable, TableArea
from .forms import RestaurantTableForm, TableAreaForm


@role_required(Role.ADMIN)
def table_admin(request):
    areas = TableArea.objects.prefetch_related("tables").filter(is_active=True)
    all_areas = TableArea.objects.all()
    tables = RestaurantTable.objects.select_related("area").all()

    area_form = TableAreaForm()
    table_form = RestaurantTableForm()

    stats = {
        "total": tables.count(),
        "available": tables.filter(status="available").count(),
        "reserved": tables.filter(status="reserved").count(),
        "occupied": tables.filter(status="occupied").count(),
        "needs_cleaning": tables.filter(status="needs_cleaning").count(),
        "disabled": tables.filter(status="disabled").count(),
    }

    return render(request, "tables/table.html", {
        "active_page": "tables",
        "areas": areas,
        "all_areas": all_areas,
        "tables": tables,
        "area_form": area_form,
        "table_form": table_form,
        "stats": stats,
    })


@role_required(Role.ADMIN)
def area_create(request):
    if request.method == "POST":
        form = TableAreaForm(request.POST)

        if form.is_valid():
            area = form.save()

            create_log(
                request,
                "create",
                "Tables",
                f"A ajouté la zone : {area.name}",
                area.id
            )

            messages.success(request, "Zone ajoutée avec succès.")
        else:
            messages.error(request, "Erreur lors de l’ajout de la zone.")

    return redirect("tables:table_admin")


@role_required(Role.ADMIN)
def area_update(request, area_id):
    area = get_object_or_404(TableArea, id=area_id)

    if request.method == "POST":
        form = TableAreaForm(request.POST, instance=area)

        if form.is_valid():
            form.save()

            create_log(
                request,
                "update",
                "Tables",
                f"A modifié la zone : {area.name}",
                area.id
            )

            messages.success(request, "Zone modifiée avec succès.")
        else:
            messages.error(request, "Erreur lors de la modification.")

    return redirect("tables:table_admin")


@role_required(Role.ADMIN)
def area_delete(request, area_id):
    area = get_object_or_404(TableArea, id=area_id)

    if request.method == "POST":
        area_name = area.name
        area.is_active = False
        area.save(update_fields=["is_active"])

        create_log(
            request,
            "delete",
            "Tables",
            f"A désactivé la zone : {area_name}",
            area.id
        )

        messages.success(request, "Zone désactivée avec succès.")

    return redirect("tables:table_admin")


@role_required(Role.ADMIN)
def table_create(request):
    if request.method == "POST":
        form = RestaurantTableForm(request.POST)

        if form.is_valid():
            table = form.save()

            create_log(
                request,
                "create",
                "Tables",
                f"A ajouté la table {table.number} dans {table.area.name}",
                table.id
            )

            messages.success(request, "Table ajoutée avec succès.")
        else:
            messages.error(request, "Erreur lors de l’ajout de la table.")

    return redirect("tables:table_admin")


@role_required(Role.ADMIN)
def table_update(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)

    if request.method == "POST":
        form = RestaurantTableForm(request.POST, instance=table)

        if form.is_valid():
            form.save()

            create_log(
                request,
                "update",
                "Tables",
                f"A modifié la table {table.number}",
                table.id
            )

            messages.success(request, "Table modifiée avec succès.")
        else:
            messages.error(request, "Erreur lors de la modification.")

    return redirect("tables:table_admin")


@role_required(Role.ADMIN)
def table_delete(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)

    if request.method == "POST":
        table.is_active = False
        table.status = "disabled"
        table.save(update_fields=["is_active", "status"])

        create_log(
            request,
            "delete",
            "Tables",
            f"A désactivé la table {table.number}",
            table.id
        )

        messages.success(request, "Table désactivée avec succès.")

    return redirect("tables:table_admin")


@role_required(Role.ADMIN)
def table_change_status(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)

    if request.method == "POST":
        old_status = table.status
        new_status = request.POST.get("status")

        table.status = new_status
        table.save(update_fields=["status"])

        create_log(
            request,
            "table",
            "Tables",
            f"Table {table.number} : {old_status} → {new_status}",
            table.id
        )

        messages.success(request, "Statut de la table mis à jour.")

    return redirect("tables:table_admin")