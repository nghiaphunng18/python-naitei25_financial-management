# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Subquery, OuterRef
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from appartment.constants import UserRole
from appartment.utils.permissions import role_required
from ...models import (
    Bill,
    RoomResident,
    RentalPrice,
    DraftBill,
    Notification,
    User,
)
from ...constants import PaymentStatus, MONTH_YEAR_FORMAT


@role_required(UserRole.RESIDENT.value)
def resident_bill_history(request):
    """
    View hiển thị lịch sử hóa đơn của cư dân
    Bao gồm tất cả hóa đơn của các phòng mà cư dân đang ở và đã từng ở
    """
    user = request.user

    # Lấy tất cả các record phòng mà user đã/đang ở
    room_residents = RoomResident.objects.filter(user=user).select_related("room")

    bill_conditions = Q()
    for rr in room_residents:
        room_condition = Q(room=rr.room)
        if rr.move_out_date:
            room_condition &= Q(
                bill_month__gte=rr.move_in_date,
                bill_month__lte=rr.move_out_date,
            )
        else:
            room_condition &= Q(bill_month__gte=rr.move_in_date)
        bill_conditions |= room_condition

    # Nếu chưa từng ở phòng nào → context rỗng
    if not bill_conditions:
        return render(
            request,
            "resident/bill_history.html",
            {
                "page_obj": None,
                "total_bills": 0,
                "paid_bills": 0,
                "unpaid_bills": 0,
                "pending_drafts": [],
                "has_pending_drafts": False,
            },
        )

    # Subquery lấy giá thuê tại bill_month
    rental_price_subquery = (
        RentalPrice.objects.filter(
            room=OuterRef("room"), effective_date__lte=OuterRef("bill_month")
        )
        .order_by("-effective_date")
        .values("price")[:1]
    )

    # Lấy danh sách bills
    bills = (
        Bill.objects.filter(bill_conditions)
        .annotate(rent_amount=Subquery(rental_price_subquery))
        .select_related("room")
        .order_by("-bill_month")
    )

    bills_list = list(bills)

    # Lấy draft bills (SENT) trong khoảng thời gian user ở
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

    # Phân trang
    paginator = Paginator(bills_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Thống kê
    total_bills = len(bills_list)
    paid_bills = sum(1 for b in bills_list if b.status == PaymentStatus.PAID.value)
    unpaid_bills = sum(1 for b in bills_list if b.status == PaymentStatus.UNPAID.value)

    context = {
        "page_obj": page_obj,
        "total_bills": total_bills,
        "paid_bills": paid_bills,
        "unpaid_bills": unpaid_bills,
        "pending_drafts": list(pending_drafts),
        "has_pending_drafts": pending_drafts.exists(),
    }
    return render(request, "resident/bill_history.html", context)


@role_required(UserRole.RESIDENT.value)
@require_POST
def confirm_draft_bill(request, pk):
    draft_bill = get_object_or_404(DraftBill, pk=pk)
    # Thêm logic kiểm tra quyền sở hữu ở đây...

    draft_bill.status = DraftBill.DraftStatus.CONFIRMED
    draft_bill.confirmed_at = timezone.now()
    draft_bill.save()

    messages.success(
        request,
        _(
            f"Đã xác nhận thành công hóa đơn nháp tháng {draft_bill.bill_month.strftime(MONTH_YEAR_FORMAT)}."
        ),
    )
    return redirect("bill_history")


@role_required(UserRole.RESIDENT.value)
@require_POST
def reject_draft_bill(request, pk):
    draft_bill = get_object_or_404(DraftBill, pk=pk)
    rejection_reason = request.POST.get("rejection_reason", _("Không có lý do."))
    # Thêm logic kiểm tra quyền sở hữu ở đây...

    draft_bill.status = DraftBill.DraftStatus.REJECTED
    draft_bill.save()

    # Tạo thông báo gửi cho các Quản lý
    title = _(f"Cư dân từ chối HĐ nháp phòng {draft_bill.room.room_id}")
    message = (
        f"Cư dân {request.user.full_name} đã từ chối hóa đơn nháp "
        f"({draft_bill.get_draft_type_display()}) cho tháng {draft_bill.bill_month.strftime(MONTH_YEAR_FORMAT)}.\n\n"
        f"Lý do: {rejection_reason}"
    )

    # Gửi đến tất cả các manager
    managers = User.objects.filter(role__role_name=UserRole.APARTMENT_MANAGER.value)
    for manager in managers:
        Notification.objects.create(
            sender=request.user, receiver=manager, title=title, message=message
        )

    messages.info(
        request, _("Bạn đã từ chối hóa đơn nháp và gửi phản hồi đến ban quản lý.")
    )
    return redirect("bill_history")
