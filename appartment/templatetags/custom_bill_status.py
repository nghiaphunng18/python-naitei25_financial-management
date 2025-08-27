from django import template
from ..constants import PaymentStatus
from ..models import DraftBill
from django.utils import timezone
from django.urls import reverse


register = template.Library()


@register.inclusion_tag("manager/bills/partials/bill_status_display.html")
def display_bill_status(bill, style="default"):
    """
    Template tag này hiển thị trạng thái hóa đơn với các style khác nhau.
    - style='default': Dạng chữ lớn (dùng cho trang chi tiết).
    - style='badge': Dạng viên thuốc/badge (dùng cho trang danh sách).
    """
    status_text = ""
    css_class = ""
    status_value = bill.status

    # Chuẩn bị các biến text
    if status_value == PaymentStatus.PAID.value:
        status_text = "Đã thanh toán"
    elif status_value == PaymentStatus.UNPAID.value:
        status_text = "Chưa thanh toán"
    elif status_value == PaymentStatus.OVERDUE.value:
        status_text = "Quá hạn"
    else:
        status_text = bill.status

    # Dựa vào tham số 'style' để chọn bộ class CSS phù hợp
    if style == "badge":
        base_badge_class = "px-3 py-1 text-xs leading-5 font-semibold rounded-full"
        if status_value == PaymentStatus.PAID.value:
            css_class = f"{base_badge_class} bg-green-100 text-green-800"
        elif status_value == PaymentStatus.UNPAID.value:
            css_class = f"{base_badge_class} bg-yellow-100 text-yellow-800"
        elif status_value == PaymentStatus.OVERDUE.value:
            css_class = f"{base_badge_class} bg-red-100 text-red-800"
        else:
            css_class = f"{base_badge_class} bg-gray-100 text-gray-800"

    else:  # style == 'default'
        base_default_class = "text-2xl font-bold"
        if status_value == PaymentStatus.PAID.value:
            css_class = f"{base_default_class} text-green-500"
        elif status_value == PaymentStatus.UNPAID.value:
            css_class = f"{base_default_class} text-yellow-500"
        elif status_value == PaymentStatus.OVERDUE.value:
            css_class = f"{base_default_class} text-red-500"
        else:
            css_class = f"{base_default_class} text-gray-500"

    return {
        "status_text": status_text,
        "css_class": css_class,
    }


@register.inclusion_tag("manager/bills/partials/draft_bill_status_tag.html")
def display_draft_bill_status(draft_bill):
    """
    Template tag để hiển thị trạng thái của hóa đơn nháp dưới dạng badge.
    """
    status_map = {
        DraftBill.DraftStatus.DRAFT: {
            "text": "Nháp",
            "css_class": "bg-gray-100 text-gray-800",
        },
        DraftBill.DraftStatus.SENT: {
            "text": "Đã gửi",
            "css_class": "bg-blue-100 text-blue-800",
        },
        DraftBill.DraftStatus.CONFIRMED: {
            "text": "Đã xác nhận",
            "css_class": "bg-green-100 text-green-800",
        },
        DraftBill.DraftStatus.REJECTED: {
            "text": "Bị từ chối",
            "css_class": "bg-red-100 text-red-800",
        },
    }

    status_info = status_map.get(
        draft_bill.status,
        {"text": draft_bill.status, "css_class": "bg-gray-100 text-gray-800"},
    )

    return {
        "status_text": status_info["text"],
        "css_class": status_info["css_class"],
    }


@register.simple_tag
def current_workspace_url():
    """
    Tạo ra URL cho trang billing workspace với tham số tháng là tháng hiện tại.
    """
    today = timezone.now().date()
    # Lấy ngày đầu tháng
    first_day_of_month = today.replace(day=1)
    # Tạo URL cơ bản
    base_url = reverse("billing_workspace")
    # Trả về URL có query string
    return f"{base_url}?month={first_day_of_month.strftime('%Y-%m-%d')}"
