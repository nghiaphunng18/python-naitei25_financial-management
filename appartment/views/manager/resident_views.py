from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q

from ...models import User, RoomResident, Notification
from ...forms.manage.resident_room_form import ResidentRoomForm
from ...constants import RoomStatus, UserRole, NotificationStatus, DEFAULT_PAGE_SIZE
from ...utils.permissions import role_required
from ...utils.resident_utils import filter_residents


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def resident_list(request):
    residents = User.objects.filter(role__role_name=UserRole.RESIDENT.value)
    context = filter_residents(request, residents)
    context["form"] = ResidentRoomForm()
    return render(request, "manager/resident/resident_list.html", context)


@require_POST
@login_required
@csrf_protect
@role_required(UserRole.APARTMENT_MANAGER.value)
def assign_room(request, user_id):
    resident = get_object_or_404(
        User, pk=user_id, role__role_name=UserRole.RESIDENT.value
    )

    form = ResidentRoomForm(request.POST, resident=resident)
    if form.is_valid():
        room = form.cleaned_data["room"]
        move_in_date = timezone.now()  # Set ngày vào là hiện tại

        # Check if resident is in selected room
        current_room = RoomResident.objects.filter(
            user=resident, room=room, move_out_date__isnull=True
        ).first()
        if current_room:
            messages.error(
                request,
                _("Cư dân đã ở phòng %(room_id)s. Vui lòng chọn phòng khác.")
                % {"room_id": room.room_id},
            )
            return redirect("resident_list")

        # Check room availability
        current_occupants = RoomResident.objects.filter(
            room=room, move_out_date__isnull=True
        ).count()
        if (
            room.status not in [RoomStatus.AVAILABLE.value, RoomStatus.OCCUPIED.value]
            or current_occupants >= room.max_occupants
        ):
            messages.error(request, _("Phòng không khả dụng hoặc đã đầy."))
            return redirect("resident_list")

        # Check if the resident is in another room
        current_room = RoomResident.objects.filter(
            user=resident, move_out_date__isnull=True
        ).first()
        if current_room:
            # Kiểm tra ngày rời phòng trước
            last_stay = (
                RoomResident.objects.filter(user=resident)
                .order_by("-move_in_date")
                .first()
            )
            if (
                last_stay
                and last_stay.move_out_date
                and move_in_date.date() <= last_stay.move_out_date.date()
            ):
                messages.error(request, _("Ngày vào phải sau ngày rời phòng trước đó."))
                return redirect("resident_list")

            current_room.move_out_date = move_in_date
            current_room.save()
            # Update old room status
            old_room_occupants = RoomResident.objects.filter(
                room=current_room.room, move_out_date__isnull=True
            ).count()
            if old_room_occupants == 0:
                current_room.room.status = RoomStatus.AVAILABLE.value
                current_room.room.save()

        # Create a new RoomResident record
        RoomResident.objects.create(
            user=resident,
            room=room,
            move_in_date=move_in_date,
        )

        # Update new room status
        room.status = RoomStatus.OCCUPIED.value
        room.save()

        # Create notification for resident
        Notification.objects.create(
            sender=request.user,
            receiver=resident,
            title=_("Gán phòng mới"),
            message=_("Bạn đã được gán vào phòng %s từ ngày %s.")
            % (room.room_id, move_in_date.strftime("%d/%m/%Y")),
            status=NotificationStatus.UNREAD.value,
        )

        messages.success(
            request,
            _("Gán phòng thành công cho cư dân %(name)s.")
            % {"name": resident.full_name},
        )
    else:
        # Hiển thị lỗi chi tiết từ form để debug
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, _(f"Lỗi ở {field}: {error}"))
        messages.error(request, _("Dữ liệu không hợp lệ. Vui lòng kiểm tra lại."))

    return redirect("resident_list")


@require_POST
@login_required
@csrf_protect
@role_required(UserRole.APARTMENT_MANAGER.value)
def leave_room(request, user_id):
    resident = get_object_or_404(
        User, pk=user_id, role__role_name=UserRole.RESIDENT.value
    )

    # Tìm xem cư dân có đang ở phòng nào không
    current_room_resident = RoomResident.objects.filter(
        user=resident, move_out_date__isnull=True
    ).first()

    if not current_room_resident:
        messages.error(request, _("Cư dân này hiện không ở trong phòng nào."))
        return redirect("resident_list")

    # Cập nhật ngày chuyển đi là hôm nay
    current_room_resident.move_out_date = timezone.now()
    current_room_resident.save()  # Lưu trước khi kiểm tra remaining

    # Nếu cư dân này là người cuối cùng rời phòng, cập nhật trạng thái phòng
    room = current_room_resident.room
    remaining = RoomResident.objects.filter(
        room=room, move_out_date__isnull=True
    ).count()
    if remaining == 0:
        room.status = RoomStatus.AVAILABLE.value
        room.save()

    current_room_resident.save()

    # Create notification for resident
    Notification.objects.create(
        sender=request.user,
        receiver=resident,
        title=_("Rời phòng"),
        message=_("Bạn đã rời khỏi phòng %s vào ngày %s.")
        % (room.room_id, timezone.now().strftime("%d/%m/%Y")),
        status=NotificationStatus.UNREAD.value,
    )

    messages.success(
        request,
        _("Đã chuyển cư dân %s ra khỏi phòng thành công.") % resident.full_name,
    )
    return redirect("resident_list")
