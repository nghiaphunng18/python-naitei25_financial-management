# templatetags/bill_filters.py
from django import template
from django.utils.translation import gettext as _
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import intcomma
import locale

register = template.Library()


@register.filter
def add_thousand_separator(value):
    """Thêm dấu phân cách hàng nghìn"""
    if value:
        try:
            return f"{int(value):,}".replace(",", ".")
        except (ValueError, TypeError):
            return value
    return ""


@register.filter
def format_currency(value):
    """Format số tiền thành định dạng tiền tệ VND"""
    if value:
        try:
            # Định dạng số với dấu phẩy ngăn cách hàng nghìn
            formatted = f"{int(value):,}".replace(",", ".")
            return mark_safe(
                f'<span class="font-semibold text-blue-600">{formatted}đ</span>'
            )
        except (ValueError, TypeError):
            return mark_safe('<span class="text-gray-400">-</span>')
    return mark_safe('<span class="text-gray-400">-</span>')


@register.filter
def payment_status_badge(status):
    """Hiển thị badge trạng thái thanh toán"""
    if status == "paid":
        return mark_safe(
            """
            <span class="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded-full inline-flex items-center">
                <i class="fas fa-check-circle mr-1"></i> Đã thanh toán
            </span>
        """
        )
    else:
        return mark_safe(
            """
            <span class="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full inline-flex items-center">
                <i class="fas fa-clock mr-1"></i> Chưa thanh toán
            </span>
        """
        )


@register.filter
def room_id_badge(room_id):
    """Hiển thị badge room ID"""
    if room_id:
        return mark_safe(
            f'<span class="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">{room_id}</span>'
        )
    return mark_safe('<span class="text-gray-400">-</span>')


@register.filter
def is_overdue(bill):
    """Kiểm tra bill có quá hạn không"""
    if bill.status == "unpaid" and bill.due_date:
        return bill.due_date.date() < timezone.now().date()
    return False


@register.filter
def format_due_date(bill):
    """Format ngày đến hạn với cảnh báo quá hạn"""
    if not bill.due_date:
        return mark_safe('<span class="text-gray-400">-</span>')

    is_overdue = (
        bill.status == "unpaid" and bill.due_date.date() < timezone.now().date()
    )
    date_class = "text-red-600" if is_overdue else "text-gray-600"
    formatted_date = bill.due_date.strftime("%d/%m/%Y")

    html = f'<div class="{date_class}">{formatted_date}'

    if is_overdue:
        html += """
            <div class="text-xs text-red-600 font-medium mt-1">
                <i class="fas fa-exclamation-triangle mr-1"></i>Quá hạn
            </div>
        """

    html += "</div>"
    return mark_safe(html)


@register.filter
def format_total_amount(value):
    """Format tổng tiền với style đặc biệt"""
    if value:
        try:
            formatted = f"{int(value):,}".replace(",", ".")
            return mark_safe(
                f'<strong class="text-lg text-blue-600">{formatted}đ</strong>'
            )
        except (ValueError, TypeError):
            return mark_safe('<span class="text-gray-400">-</span>')
    return mark_safe('<span class="text-gray-400">-</span>')
