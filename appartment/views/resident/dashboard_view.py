from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ...models import Bill, RoomResident, Notification, DraftBill
from ...utils.permissions import role_required
from ...constants import UserRole, PaymentStatus
from django.db.models import Q


@role_required(UserRole.RESIDENT.value)
def resident_dashboard(request, context=None):
    user = request.user

    # Lấy tất cả phòng mà cư dân này ở (chưa move_out thì coi là đang ở)
    room_ids = RoomResident.objects.filter(
        user=user, move_out_date__isnull=True
    ).values_list("room_id", flat=True)

    # Tổng số phòng đang ở
    current_rooms = room_ids.count()
    room_residents = RoomResident.objects.filter(user=user).select_related("room")
    # Hóa đơn theo phòng cư dân
    unpaid_bills = Bill.objects.filter(
        room_id__in=room_ids, status=PaymentStatus.UNPAID.value
    ).count()
    paid_bills = Bill.objects.filter(
        room_id__in=room_ids, status=PaymentStatus.PAID.value
    ).count()

    pending_drafts = DraftBill.objects.none()
    for rr in room_residents:
        qs = DraftBill.objects.filter(
            room=rr.room,
            status=DraftBill.DraftStatus.SENT,
            bill_month__gte=rr.move_in_date,
        )
        if rr.move_out_date:
            qs = qs.filter(bill_month__lte=rr.move_out_date)
        pending_drafts |= qs

    # Thông báo gần nhất (receiver là user hiện tại)
    latest_notifications = Notification.objects.filter(receiver=user).order_by(
        "-created_at"
    )[:5]

    if context is None:
        context = {}

    context.update(
        {
            "current_rooms": current_rooms,
            "unpaid_bills": unpaid_bills,
            "paid_bills": paid_bills,
            "latest_notifications": latest_notifications,
            "pending_drafts": list(pending_drafts),
            "has_pending_drafts": pending_drafts.exists(),
        }
    )
    return render(request, "resident/dashboard.html", context)
