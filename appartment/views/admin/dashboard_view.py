from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from ...models import User, Room, Bill, Notification
from ...constants import UserRole, RoomStatus, PaymentStatus, NotificationStatus
from ...utils.permissions import role_required


@login_required
@role_required(UserRole.ADMIN.value)
def admin_dashboard(request, context=None):
    if context is None:
        context = {}
    context.update(
        {
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(is_active=True).count(),
            "inactive_users": User.objects.filter(is_active=False).count(),
            "total_rooms": Room.objects.count(),
            "available_rooms": Room.objects.filter(
                status=RoomStatus.AVAILABLE.value
            ).count(),
            "total_bills": Bill.objects.count(),
            "unpaid_bills": Bill.objects.filter(
                status=PaymentStatus.UNPAID.value
            ).count(),
            "total_notifications": Notification.objects.count(),
            "unread_notifications": Notification.objects.filter(
                status=NotificationStatus.UNREAD.value
            ).count(),
        }
    )
    return render(request, "admin/dashboard.html", context)
