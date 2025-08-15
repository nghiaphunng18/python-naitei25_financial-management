from datetime import datetime

from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from django.contrib import messages

from ..constants import DEFAULT_PAGE_SIZE, NotificationStatus


def filter_notifications(request, base_query):
    """
    Helper function để lọc, tìm kiếm và phân trang thông báo.
    Args:
        request: Request object chứa các tham số GET.
        base_query: QuerySet cơ bản của thông báo theo role.
    Returns:
        context: chứa danh sách thông báo phân trang và context.
    """
    # Lấy các tham số từ GET
    sort_by = request.GET.get("sort_by", "newest")
    filter_type = request.GET.get("filter_type", "all")
    filter_month = request.GET.get("filter_month", "")
    filter_date = request.GET.get("filter_date", "")
    search_query = request.GET.get("search_query", "")

    notifications = base_query

    # Lọc theo tháng
    if filter_month:
        try:
            year, month = map(int, filter_month.split("-"))
            notifications = notifications.filter(
                created_at__year=year, created_at__month=month
            )
        except ValueError:
            messages.error(request, _("Định dạng tháng không hợp lệ."))
            notifications = notifications.none()  # empty queryset

    # Lọc theo ngày
    if filter_date:
        try:
            date = datetime.strptime(filter_date, "%Y-%m-%d")
            notifications = notifications.filter(created_at__date=date)
        except ValueError:
            messages.error(request, _("Định dạng ngày không hợp lệ."))
            notifications = notifications.none()  # empty queryset

    # Tìm kiếm
    if search_query:
        notifications = notifications.filter(
            Q(title__icontains=search_query)
            | Q(message__icontains=search_query)
            | Q(sender__full_name__icontains=search_query)
        )

    # Sắp xếp
    if sort_by == "newest":
        notifications = notifications.order_by("-created_at")
    elif sort_by == "oldest":
        notifications = notifications.order_by("created_at")

    # Phân trang
    paginator = Paginator(notifications, DEFAULT_PAGE_SIZE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Thêm status_display và status_color cho từng thông báo thay vì xử lý logic ở template
    notifications_with_status = []
    for notification in page_obj:
        status_display = (
            _("Chưa đọc")
            if notification.status == NotificationStatus.UNREAD.value
            else _("Đã đọc")
        )
        status_color = (
            "text-red-600"
            if notification.status == NotificationStatus.UNREAD.value
            else "text-green-600"
        )
        notifications_with_status.append(
            {
                "notification": notification,
                "status_display": status_display,
                "status_color": status_color,
            }
        )

    context = {
        "notifications": page_obj,
        "notifications_with_status": notifications_with_status,
        "sort_by": sort_by,
        "filter_type": filter_type,
        "filter_month": filter_month,
        "filter_date": filter_date,
        "search_query": search_query,
    }

    # Tạo query_params cho phân trang
    query_params = []
    if sort_by:
        query_params.append(f"sort_by={sort_by}")
    if filter_type:
        query_params.append(f"filter_type={filter_type}")
    if filter_month:
        query_params.append(f"filter_month={filter_month}")
    if filter_date:
        query_params.append(f"filter_date={filter_date}")
    if search_query:
        query_params.append(f"search_query={search_query}")
    query_params = "&".join(query_params)
    context["query_params"] = query_params

    return context
