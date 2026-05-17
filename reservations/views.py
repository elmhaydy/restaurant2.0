from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail

from .forms import ReservationForm
from .models import Reservation, ReservationStatus
from tables.models import RestaurantTable, TableStatus
from admin_panel.utils import create_log
from django.http import JsonResponse


def create_reservation(request):
    guests = request.POST.get("guests") or request.GET.get("guests")

    form = ReservationForm(
        request.POST or None,
        guests=int(guests) if guests else None
    )

    available_tables = RestaurantTable.objects.none()

    if request.method == "POST":
        guests = request.POST.get("guests")
        date = request.POST.get("date")
        time = request.POST.get("time")

        if guests and date and time:
            reserved_tables_ids = Reservation.objects.filter(
                date=date,
                time=time,
                status__in=[
                    ReservationStatus.PENDING,
                    ReservationStatus.CONFIRMED,
                    ReservationStatus.SEATED,
                ]
            ).exclude(table=None).values_list("table_id", flat=True)

            available_tables = RestaurantTable.objects.filter(
                is_active=True,
                capacity__gte=guests,
                status=TableStatus.AVAILABLE
            ).exclude(id__in=reserved_tables_ids).order_by("zone", "capacity", "number")

        if form.is_valid():
            reservation = form.save(commit=False)

            selected_table = reservation.table

            if not selected_table:
                messages.error(request, "Veuillez choisir une table disponible.")
                return render(request, "public/reservation.html", {
                    "form": form,
                    "available_tables": available_tables,
                })

            table_already_reserved = Reservation.objects.filter(
                table=selected_table,
                date=reservation.date,
                time=reservation.time,
                status__in=[
                    ReservationStatus.PENDING,
                    ReservationStatus.CONFIRMED,
                    ReservationStatus.SEATED,
                ]
            ).exists()

            if (
                selected_table.status != TableStatus.AVAILABLE
                or selected_table.capacity < reservation.guests
                or table_already_reserved
            ):
                messages.error(request, "Cette table n’est plus disponible pour ce créneau.")
                return render(request, "public/reservation.html", {
                    "form": form,
                    "available_tables": available_tables,
                })

            reservation.user = request.user if request.user.is_authenticated else None
            reservation.status = ReservationStatus.PENDING
            reservation.save()

            # On réserve provisoirement la table dès la demande
            selected_table.status = TableStatus.RESERVED
            selected_table.save(update_fields=["status"])

            create_log(
                request,
                "reservation",
                "Réservations",
                f"Nouvelle réservation client : {reservation.full_name}",
                reservation.id
            )

            if reservation.email:
                from django.conf import settings
                send_mail(
                    "Réservation reçue",
                    "Votre réservation a été reçue. Nous vérifions la disponibilité et vous recevrez une confirmation.",
                    settings.DEFAULT_FROM_EMAIL,
                    [reservation.email],
                    fail_silently=True,
                )

            messages.success(request, "Réservation envoyée. Vous recevrez une confirmation après validation.")
            return redirect("reservations:my_reservations")

    return render(request, "public/reservation.html", {
        "form": form,
        "available_tables": available_tables,
    })

@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).select_related("table")

    return render(request, "public/my_reservations.html", {
        "reservations": reservations,
    })


@login_required
def cancel_my_reservation(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user
    )

    if request.method == "POST" and reservation.status in ["pending", "confirmed"]:
        reservation.status = ReservationStatus.CANCELLED
        reservation.save(update_fields=["status"])

        if reservation.table:
            reservation.table.status = TableStatus.AVAILABLE
            reservation.table.save(update_fields=["status"])

        messages.success(request, "Votre réservation a été annulée.")

    return redirect("reservations:my_reservations")


def available_tables(request):
    guests = request.GET.get("guests")
    date = request.GET.get("date")
    time = request.GET.get("time")

    try:
        guests = int(guests)
    except (TypeError, ValueError):
        return JsonResponse({"tables": []})

    reserved_tables_ids = []

    if date and time:
        reserved_tables_ids = Reservation.objects.filter(
            date=date,
            time=time,
            status__in=[
                ReservationStatus.PENDING,
                ReservationStatus.CONFIRMED,
                ReservationStatus.SEATED,
            ]
        ).exclude(table=None).values_list("table_id", flat=True)

    tables = RestaurantTable.objects.filter(
        is_active=True,
        status=TableStatus.AVAILABLE,
        capacity__gte=guests,
    ).exclude(
        id__in=reserved_tables_ids
    ).order_by("zone", "capacity", "number")

    data = [
        {
            "id": table.id,
            "label": f"{table.name} - {table.get_zone_display()} - {table.capacity} personnes"
        }
        for table in tables
    ]

    return JsonResponse({"tables": data})