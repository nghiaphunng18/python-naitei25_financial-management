from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from ..forms.manage.notification_form import NotificationForm
from ..models import Notification, User
from ..constants import UserRole, NotificationStatus
from ..utils.permissions import role_required


@login_required
@role_required(UserRole.RESIDENT.value)
def resident_send_notification(request):
    """
    Form gửi thông báo cho Resident (receiver=null).
    """
    if request.method == "POST":
        form = NotificationForm(request.POST, sender_role=UserRole.RESIDENT.value)
        if form.is_valid():
            Notification.objects.create(
                sender=request.user,
                receiver=None,  # Hệ thống
                title=form.cleaned_data["title"],
                message=form.cleaned_data["message"],
                status=NotificationStatus.UNREAD.value,
            )
            messages.success(request, _("Thông báo đã được gửi thành công."))
            return redirect("resident_notification_history")
    else:
        form = NotificationForm(sender_role=UserRole.RESIDENT.value)
    return render(
        request, "resident/notifications/send_notification.html", {"form": form}
    )


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def manager_send_notification(request):
    """
    Form gửi thông báo cho Manager (receiver_type -> load receiver).
    """
    if request.method == "POST":
        form = NotificationForm(
            request.POST, sender_role=UserRole.APARTMENT_MANAGER.value
        )
        selected_receivers = request.POST.getlist("receiver", [])
        if form.is_valid():
            receiver_type = form.cleaned_data["receiver_type"]
            send_all = form.cleaned_data.get("send_all", False)
            title = form.cleaned_data["title"]
            message = form.cleaned_data["message"]

            role_map = {
                "admin": UserRole.ADMIN.value,
                "manager": UserRole.APARTMENT_MANAGER.value,
                "resident": UserRole.RESIDENT.value,
            }
            expected_role = role_map.get(receiver_type)

            receivers = set()
            if send_all:
                receivers.update(
                    User.objects.filter(
                        role__role_name=expected_role, is_active=True
                    ).values_list("user_id", flat=True)
                )
            if selected_receivers:
                receivers.update(selected_receivers)

            if not receivers:
                messages.error(
                    request,
                    _("Vui lòng chọn ít nhất một người nhận hoặc tích gửi cho tất cả."),
                )
            else:
                for receiver_id in receivers:
                    try:
                        receiver = User.objects.get(user_id=receiver_id)
                        Notification.objects.create(
                            sender=request.user,
                            receiver=receiver,
                            title=title,
                            message=message,
                            status=NotificationStatus.UNREAD.value,
                        )
                    except User.DoesNotExist:
                        messages.error(
                            request,
                            _(f"Người nhận với ID {receiver_id} không tồn tại."),
                        )
                        continue
                messages.success(request, _("Thông báo đã được gửi thành công."))
                return redirect("manager_notification_history")
        else:
            messages.error(request, _("Form không hợp lệ. Vui lòng kiểm tra lại."))
    else:
        form = NotificationForm(sender_role=UserRole.APARTMENT_MANAGER.value)
    return render(
        request, "manager/notifications/send_notification.html", {"form": form}
    )


@login_required
@role_required(UserRole.ADMIN.value)
def admin_send_notification(request):
    """
    Form gửi thông báo cho Admin (receiver_type -> load receiver).
    """
    if request.method == "POST":
        form = NotificationForm(request.POST, sender_role=UserRole.ADMIN.value)
        selected_receivers = request.POST.getlist("receiver", [])
        if form.is_valid():
            receiver_type = form.cleaned_data["receiver_type"]
            send_all = form.cleaned_data.get("send_all", False)
            title = form.cleaned_data["title"]
            message = form.cleaned_data["message"]

            role_map = {
                "admin": UserRole.ADMIN.value,
                "manager": UserRole.APARTMENT_MANAGER.value,
                "resident": UserRole.RESIDENT.value,
            }
            expected_role = role_map.get(receiver_type)

            receivers = set()
            if send_all:
                receivers.update(
                    User.objects.filter(
                        role__role_name=expected_role, is_active=True
                    ).values_list("user_id", flat=True)
                )
            if selected_receivers:
                receivers.update(selected_receivers)

            if not receivers:
                messages.error(
                    request,
                    _("Vui lòng chọn ít nhất một người nhận hoặc tích gửi cho tất cả."),
                )
            else:
                for receiver_id in receivers:
                    try:
                        receiver = User.objects.get(user_id=receiver_id)
                        Notification.objects.create(
                            sender=request.user,
                            receiver=receiver,
                            title=title,
                            message=message,
                            status=NotificationStatus.UNREAD.value,
                        )
                    except User.DoesNotExist:
                        messages.error(
                            request,
                            _(f"Người nhận với ID {receiver_id} không tồn tại."),
                        )
                        continue
                messages.success(request, _("Thông báo đã được gửi thành công."))
                return redirect("admin_notification_history")
        else:
            messages.error(request, _("Form không hợp lệ. Vui lòng kiểm tra lại."))
    else:
        form = NotificationForm(sender_role=UserRole.ADMIN.value)
    return render(request, "admin/notifications/send_notification.html", {"form": form})


@require_POST
@login_required
@csrf_protect
def load_users_by_role(request):
    """
    AJAX load danh sách user active dựa trên receiver_type.
    """
    receiver_type = request.POST.get("receiver_type")
    users = User.objects.filter(is_active=True)

    if receiver_type == "admin":
        users = users.filter(role__role_name=UserRole.ADMIN.value)
    elif receiver_type == "manager":
        users = users.filter(role__role_name=UserRole.APARTMENT_MANAGER.value)
    elif receiver_type == "resident":
        users = users.filter(role__role_name=UserRole.RESIDENT.value)
    else:
        return JsonResponse({"users": []})

    user_list = [
        {"id": user.user_id, "name": user.full_name}
        for user in users.order_by("full_name")
    ]
    return JsonResponse({"users": user_list})
