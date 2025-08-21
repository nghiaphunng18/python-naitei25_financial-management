from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from appartment.models.rental_prices import RentalPrice
from appartment.utils.permissions import role_required
from ...models import Room, RoomResident, User
from ...constants import (
    PRICE_CHANGES_PER_PAGE_MAX,
    HISTORY_PER_PAGE_MAX,
    UserRole,
    DAY_MONTH_YEAR_FORMAT,
    MONTH_YEAR_FORMAT,
)


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def get_room_history(request, room_id):
    """
    View để xem lịch sử thay đổi phòng cho quản lý
    """
    # 1. Changing room's prices - left card
    # 2. Details about room history every month - right card
    #   (include: month | price | status | list of residents)

    # 1
    try:
        room = Room.objects.get(room_id=room_id)
    except Room.DoesNotExist:
        messages.error(request, _(f"Phòng có ID {room_id} không tồn tại."))
        return redirect("room_list")

    # 2:
    # - Create month_list from room's created_at to current month
    # - Get all changed prices of room_id (table rental_prices)
    # - Get all residents who lived or living in room_id
    # - For each month in month_list, get price of month,  get the list of residents who lived in that month

    month_list = []
    current = room.created_at.date().replace(day=1)
    today = date.today().replace(day=1)

    while current <= today:
        month_list.append(current)
        current += relativedelta(months=1)
    month_list.reverse()

    prices = RentalPrice.objects.filter(room_id=room_id).order_by("-effective_date")

    residents = RoomResident.objects.filter(room_id=room_id).select_related("user")

    history = []

    for month_start in month_list:
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
        price_in_month = None
        price_in_month = (
            prices.filter(effective_date__date__lte=month_end)
                .order_by("-effective_date")
                .first()
        )
        price_in_month = price_in_month.price if price_in_month else None

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
        "base_template": "base_manager.html",
        "back_url": "room_detail",
        "room": room,
        "price_page_obj": price_page_obj,
        "history_page_obj": history_page_obj,
    }

    template_name = "room_history.html"
    return render(request, template_name, context)
