from calendar import monthrange
from datetime import datetime
import json
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from collections import OrderedDict

from appartment.utils.permissions import role_required

from ...models import Room, RoomResident, Bill
from ...constants import UserRole, RoomStatus, PaymentStatus


@role_required(UserRole.APARTMENT_MANAGER.value)
def manager_dashboard(request, context=None):
    # 1
    total_rooms = Room.objects.count()

    # 2
    now = timezone.now()
    total_residents = RoomResident.objects.filter(
        Q(move_out_date__isnull=True) | Q(move_out_date__gt=now)
    ).count()

    # 3
    if now.day < 25:
        total_bill_month = now - relativedelta(months=1)
    else:
        total_bill_month = now

    bills = Bill.objects.filter(
        bill_month__year=total_bill_month.year, bill_month__month=total_bill_month.month
    )

    # 4
    total_bill_money = bills.aggregate(total=Sum("total_amount"))["total"] or 0

    # 5
    total_occupied_rooms = Room.objects.filter(status=RoomStatus.OCCUPIED.value).count()

    # 6
    # Lọc ra các hóa đơn đã thanh toán cua thang do
    total_paid_bills = bills.filter(status=PaymentStatus.PAID.value)

    # Tổng số hóa đơn đã thanh toán
    total_paid_count = total_paid_bills.count()

    # Tổng số tiền đã thanh toán
    total_paid_money = (
        total_paid_bills.aggregate(total=Sum("total_amount"))["total"] or 0
    )

    # 7
    overdue_bills = Bill.objects.filter(
        due_date__lt=now,  # due_date nhỏ hơn hiện tại
        status=PaymentStatus.UNPAID.value,  # trạng thái chưa thanh toán
    ).order_by("-due_date")
    # 8
    months = OrderedDict()
    for i in range(5, -1, -1):
        month_date = now - relativedelta(months=i)
        month_key = month_date.strftime("%Y-%m")
        months[month_key] = 0

    # Tổng hợp theo từng tháng bằng year và month
    for month_key in months.keys():
        year, month = map(int, month_key.split("-"))

        total = (
            Bill.objects.filter(
                bill_month__year=year, bill_month__month=month
            ).aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        months[month_key] = float(total)
    context.update(
        {
            "total_rooms": total_rooms,
            "total_residents": total_residents,
            "total_bill_month": total_bill_month,
            "total_bills": bills.count(),
            "total_bill_money": total_bill_money,
            "total_occupied_rooms": total_occupied_rooms,
            "total_paid_count": total_paid_count,
            "total_paid_money": total_paid_money,
            "overdue_bills": overdue_bills,
            "months_labels": json.dumps(list(months.keys())),
            "months_amounts": json.dumps(list(months.values())),
        }
    )

    return render(request, "manager/dashboard.html", context)
