from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.core.paginator import Paginator


from ...models import Room, RoomResident, User, RentalPrice
from appartment.utils.permissions import role_required
from ...constants import (
    DAY_MONTH_YEAR_FORMAT,
    HISTORY_PER_PAGE_MAX,
    MONTH_YEAR_FORMAT,
    PRICE_CHANGES_PER_PAGE_MAX,
    UserRole,
)


@login_required
@role_required(UserRole.RESIDENT.value)
def room_list(request):
    """
    View để xem danh sách các phòng đang ở và đã ở cho cư dân
    """
    user_id = request.user.user_id
    user_name = request.user.full_name
    today = now().date()

    # Get all room residents for the user
    room_residents = RoomResident.objects.filter(user_id=user_id).select_related("room")
    room_infos = []

    if not room_residents.exists():
        messages.error(request, _(f"ID {user_id} không tồn tại."))
        return redirect("dashboard")

    for rr in room_residents:
        room = rr.room
        move_in = rr.move_in_date.date()
        move_out = rr.move_out_date.date() if rr.move_out_date else None

        # Status
        is_current = (not move_out) or (move_out >= today)
        status = _("Đang ở") if is_current else _("Đã rời đi")

        # remaining slots onlyif the resident is currently in the room
        remaining_slots = None
        if is_current:
            current_residents = RoomResident.objects.filter(
                room_id=room.room_id,
                move_in_date__lte=today,
                move_out_date__isnull=True,
            ) | RoomResident.objects.filter(
                room_id=room.room_id, move_in_date__lte=today, move_out_date__gte=today
            )
            current_count = current_residents.count()
            remaining_slots = room.max_occupants - current_count

        room_infos.append(
            {
                "room_id": room.room_id,
                "area": room.area,
                "max_occupants": room.max_occupants,
                "move_in_date": move_in,
                "move_out_date": move_out,
                "status": status,
                "remaining_slots": remaining_slots,
            }
        )

    context = {"user_id": user_id, "user_name": user_name, "room_infos": room_infos}
    return render(request, "resident/rooms/room_list.html", context)


@login_required
@role_required(UserRole.RESIDENT.value)
def room_detail(request, room_id):
    """
    View để xem thông tin chi tiết về 1 phòng cho cư dân
    """
    # Get general information about the room
    # if the room is currently occupied, show the current residents from move in date to today
    # if the room is not currently occupied, show the history of residents from move in date to move out date

    user_id = request.user.user_id

    try:
        room_resident = RoomResident.objects.select_related("room").get(
            room_id=room_id, user_id=user_id
        )
    except RoomResident.DoesNotExist:
        messages.error(
            request, _("Phòng có ID %(room_id)s không tồn tại.") % {"room_id": room_id}
        )
        return redirect("resident_room_list")

    today = now().date()
    move_in = room_resident.move_in_date.date()
    move_out = (
        room_resident.move_out_date.date() if room_resident.move_out_date else None
    )
    is_current = (not move_out) or (move_out >= today)
    status = _("Đang ở") if is_current else _("Đã rời đi")

    remaining_slots = None
    current_residents = None
    current_rental_room = None
    history_residents = None

    if is_current:
        current_residents = RoomResident.objects.filter(
            room_id=room_id,
            move_in_date__lte=today,
            move_out_date__isnull=True,
        ).select_related("user") | RoomResident.objects.filter(
            room_id=room_id, move_in_date__lte=today, move_out_date__gte=today
        ).select_related(
            "user"
        )
        current_residents_count = current_residents.count()
        remaining_slots = room_resident.room.max_occupants - current_residents_count

        current_rental_room = (
            RentalPrice.objects.filter(room_id=room_id, effective_date__lte=today)
            .order_by("-effective_date")
            .first()
        )
    else:
        history_residents = RoomResident.objects.filter(
            room_id=room_id, move_in_date__lte=move_out, move_out_date__gte=move_in
        ).select_related("user") | RoomResident.objects.filter(
            room_id=room_id, move_in_date__lte=move_out, move_out_date__isnull=True
        ).select_related(
            "user"
        )

    context = {
        "room_id": room_id,
        "status": status,
        "area": room_resident.room.area,
        "max_occupants": room_resident.room.max_occupants,
        "description": room_resident.room.description,
        "created_at": room_resident.room.created_at,
        "move_in_date": move_in,
        "move_out_date": move_out,
        "remaining_slots": remaining_slots,
        "current_residents": current_residents,
        "current_rental_price": (
            current_rental_room.price if current_rental_room else None
        ),
        "history_residents": history_residents,
    }
    return render(request, "resident/rooms/room_detail.html", context)


@login_required
@role_required(UserRole.RESIDENT.value)
def room_history(request, room_id):
    """
    View để xem lịch sử thay đổi phòng cho cư dân
    """

    user_id = request.user.user_id
    try:
        room = RoomResident.objects.get(room_id=room_id, user_id=user_id)
    except RoomResident.DoesNotExist:
        messages.error(
            request, _("Phòng có ID %(room_id)s không tồn tại.") % {"room_id": room_id}
        )
        return redirect("resident_room_list")

    # Month list from move_in_date to move_out_date or today
    month_list = []
    current = room.move_in_date.date().replace(day=1)
    move_out_date = (
        room.move_out_date.date().replace(day=1)
        if room.move_out_date
        else date.today().replace(day=1)
    )

    while current <= move_out_date:
        month_list.append(current)
        current += relativedelta(months=1)
    month_list.reverse()

    prices = list(
        RentalPrice.objects.filter(
            room_id=room_id,
            effective_date__gt=room.move_in_date,
            effective_date__lte=move_out_date or date.today(),
        ).order_by("effective_date")
    )

    # Get initial price before move-in date
    initial_price = (
        RentalPrice.objects.filter(
            room_id=room_id, effective_date__lte=room.move_in_date
        )
        .order_by("-effective_date")
        .first()
    )

    # Add initial price to the first of prices list and alter its effective date to move_in_date
    if initial_price:
        initial_price.effective_date = room.move_in_date
        prices.insert(0, initial_price)

    residents = RoomResident.objects.filter(room_id=room_id).select_related("user")

    history = []

    for month_start in month_list:
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

        price_in_month = None
        for p in prices:
            if p.effective_date.date() <= month_end:
                price_in_month = p.price
            else:
                break

        users_in_month = [
            {"full_name": res.user.full_name, "user_id": res.user.user_id}
            for res in residents
            if res.move_in_date.date() <= month_end
            and (res.move_out_date is None or res.move_out_date.date() >= month_start)
        ]

        history.append(
            {
                "month": month_start,
                "number_of_residents": len(users_in_month),
                "residents": users_in_month,
                "price": price_in_month,
            }
        )

    # Paginate general_change_price
    price_changes = [
        {
            "price": p.price,
            "effective_date": p.effective_date,
        }
        for p in prices
    ]
    price_paginator = Paginator(price_changes, PRICE_CHANGES_PER_PAGE_MAX)
    price_page_number = request.GET.get("page1")
    price_page_obj = price_paginator.get_page(price_page_number)

    # Paginate history
    history_paginator = Paginator(history, HISTORY_PER_PAGE_MAX)
    history_page_number = request.GET.get("page2")
    history_page_obj = history_paginator.get_page(history_page_number)

    context = {
        "room_id": room_id,
        "base_template": "base_resident.html",
        "back_url": "resident_room_detail",
        "room": room,
        "price_page_obj": price_page_obj,
        "history_page_obj": history_page_obj,
    }

    template_name = "room_history.html"
    return render(request, template_name, context)
