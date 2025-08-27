from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from django.core.paginator import Paginator

from ..models import Notification
from ..constants import NotificationStatus, UserRole
from ..utils.permissions import role_required
from ..utils.notification_utils import filter_notifications

"""
sender: ROLE_RESIDENT -> receiver: null (ROLE_ADMIN + ROLE_APARTMENT_MANAGER)
sender: ROLE_APARTMENT_MANAGER -> receiver: ROLE_RESIDENT | ROLE_ADMIN | ROLE_MANAGER
sender: ROLE_ADMIN -> receiver: ROLE_RESIDENT | ROLE_ADMIN | ROLE_MANAGER
"""


def notification_history(request, role, base_query, template_name, filter_types=None):
    """
    Hàm chung để hiển thị lịch sử thông báo cho các role.
    """
    notifications = base_query.select_related("sender", "receiver")

    # Lọc theo loại thông báo
    filter_type = request.GET.get("filter_type", "all")
    if filter_types and filter_type != "all" and filter_type not in filter_types:
        filter_type = "all"

    if role == UserRole.APARTMENT_MANAGER.value and filter_type != "all":
        if filter_type == "from_resident":
            notifications = notifications.filter(
                receiver__isnull=True, sender__role__role_name=UserRole.RESIDENT.value
            )
        elif filter_type == "from_admin":
            notifications = notifications.filter(
                sender__role__role_name=UserRole.ADMIN.value
            )
        elif filter_type == "to_manager":
            notifications = notifications.filter(receiver=request.user)
        elif filter_type == "by_manager":
            notifications = notifications.filter(sender=request.user)
    elif role == UserRole.ADMIN.value and filter_type != "all":
        if filter_type == "to_admin":
            notifications = notifications.filter(receiver=request.user)
        elif filter_type == "by_admin":
            notifications = notifications.filter(sender=request.user)
        elif filter_type == "from_resident":
            notifications = notifications.filter(
                receiver__isnull=True, sender__role__role_name=UserRole.RESIDENT.value
            )
    elif role == UserRole.RESIDENT.value and filter_type != "all":
        if filter_type == "to_me":
            notifications = notifications.filter(receiver=request.user)
        elif filter_type == "by_me":
            notifications = notifications.filter(sender=request.user)

    context = filter_notifications(request, notifications)
    context["filter_type"] = filter_type
    return render(request, template_name, context)


@login_required
@role_required(UserRole.RESIDENT.value)
def resident_notification_history(request):
    """
    Hiển thị lịch sử thông báo cho người thuê.
    """
    notifications = Notification.objects.filter(
        Q(receiver=request.user) | Q(sender=request.user)
    )
    return notification_history(
        request,
        UserRole.RESIDENT.value,
        notifications,
        "resident/notifications/history_notifications.html",
        filter_types=["to_me", "by_me"],
    )


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def manager_notification_history(request):
    """
    Hiển thị lịch sử thông báo cho người quản lý chung cư.
    """
    notifications = Notification.objects.filter(
        Q(
            receiver__isnull=True, sender__role__role_name=UserRole.RESIDENT.value
        )  # Từ người thuê gửi lên hệ thống
        | Q(receiver=request.user)  # Dành riêng cho chính người quản lý
        | Q(
            sender=request.user
        )  # Do chính người quản lý gửi (gán phòng, rời phòng, ...)
    )

    return notification_history(
        request,
        UserRole.APARTMENT_MANAGER.value,
        notifications,
        "manager/notifications/history_notifications.html",
        filter_types=["from_resident", "from_admin", "to_manager", "by_manager"],
    )


@login_required
@role_required(UserRole.ADMIN.value)
def admin_notification_history(request):
    """
    Hiển thị lịch sử thông báo cho admin.
    """
    notifications = Notification.objects.filter(
        Q(
            receiver__isnull=True, sender__role__role_name=UserRole.RESIDENT.value
        )  # Từ người thuê gửi lên hệ thống
        | Q(receiver=request.user)  # Dành riêng cho admin
        | Q(sender=request.user)  # Do admin gửi
    )

    return notification_history(
        request,
        UserRole.ADMIN.value,
        notifications,
        "admin/notifications/history_notifications.html",
        filter_types=["from_resident", "to_admin", "by_admin"],
    )


@require_POST
@login_required
@csrf_protect
def mark_notification_read(request, notification_id):
    """
    Đánh dấu thông báo là đã đọc.
    """
    notification = get_object_or_404(Notification, pk=notification_id)

    # Kiểm tra quyền truy cập thông báo
    if not (
        (
            notification.receiver is None
            and notification.sender.role.role_name == UserRole.RESIDENT.value
        )
        or (notification.sender.role.role_name == UserRole.ADMIN.value)
        or (notification.receiver == request.user)
        or (notification.sender == request.user)
    ):
        messages.error(request, _("Bạn không có quyền xem thông báo này."))
        return redirect("notification_history")

    try:
        notification.status = NotificationStatus.READ.value
        notification.save()
        messages.success(request, _("Thông báo đã được đánh dấu là đã đọc."))
    except Exception as e:
        messages.error(request, _("Có lỗi xảy ra khi đánh dấu thông báo: %s") % str(e))

    role = request.user.role.role_name
    if role == UserRole.RESIDENT.value:
        return redirect("resident_notification_history")
    elif role == UserRole.APARTMENT_MANAGER.value:
        return redirect("manager_notification_history")
    elif role == UserRole.ADMIN.value:
        return redirect("admin_notification_history")
    return redirect("dashboard")
