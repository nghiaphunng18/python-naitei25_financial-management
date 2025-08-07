# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Subquery, OuterRef
from django.utils import timezone

from appartment.constants import UserRole
from appartment.utils.permissions import role_required
from ...models import (
    Bill,
    RoomResident,
    RentalPrice,
)


@role_required(UserRole.RESIDENT.value)
def resident_bill_history(request):
    """
    View hiển thị lịch sử hóa đơn của cư dân
    Bao gồm tất cả hóa đơn của các phòng mà cư dân đang ở và đã từng ở
    """
    user = request.user

    # Lấy tất cả các phòng mà user đang ở và đã từng ở
    room_residents = RoomResident.objects.filter(user=user).select_related("room")

    # Tạo danh sách các điều kiện để lọc bill
    bill_conditions = Q()

    for room_resident in room_residents:
        room = room_resident.room
        move_in_date = room_resident.move_in_date
        move_out_date = room_resident.move_out_date

        # Điều kiện cơ bản: bill thuộc về phòng này
        room_condition = Q(room=room)

        # Nếu vẫn đang ở (move_out_date = None)
        if move_out_date is None:
            # Lấy tất cả bill từ ngày move_in đến hiện tại
            room_condition &= Q(bill_month__gte=move_in_date)
        else:
            # Nếu đã chuyển đi, chỉ lấy bill trong khoảng thời gian ở
            room_condition &= Q(
                bill_month__gte=move_in_date, bill_month__lte=move_out_date
            )

        bill_conditions |= room_condition

    # Kiểm tra nếu không có điều kiện nào (user chưa từng ở phòng nào)
    if not bill_conditions:
        # Trả về context với dữ liệu rỗng
        context = {
            "page_obj": None,
            "total_bills": 0,
            "paid_bills": 0,
            "unpaid_bills": 0,
        }
        return render(request, "resident/bill_history.html", context)

    # Subquery để lấy rental price hiệu lực tại thời điểm bill_month
    rental_price_subquery = (
        RentalPrice.objects.filter(
            room=OuterRef("room"), effective_date__lte=OuterRef("bill_month")
        )
        .order_by("-effective_date")
        .values("price")[:1]  # Chỉ lấy giá trị price, không lấy toàn bộ object
    )

    # Lấy tất cả bill thỏa mãn điều kiện với rental price
    bills = (
        Bill.objects.filter(bill_conditions)
        .annotate(rent_amount=Subquery(rental_price_subquery))
        .select_related("room")
        .order_by("-bill_month")
    )

    # Chuyển đổi QuerySet thành list để tính toán thống kê
    bills_list = list(bills)

    # Phân trang: 10 hóa đơn/trang
    paginator = Paginator(bills_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Tính toán thống kê
    total_bills = len(bills_list)
    paid_bills = sum(1 for bill in bills_list if bill.status == "paid")
    unpaid_bills = sum(1 for bill in bills_list if bill.status in ["unpaid"])

    context = {
        "page_obj": page_obj,
        "total_bills": total_bills,
        "paid_bills": paid_bills,
        "unpaid_bills": unpaid_bills,
    }

    return render(request, "resident/bill_history.html", context)
