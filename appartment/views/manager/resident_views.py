from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.shortcuts import get_object_or_404

from ...models import User, RoomResident, Room, Province, District, Ward, Notification
from ...forms.manage.resident_room_form import ResidentRoomForm
from ...constants import RoomStatus, UserRole
from ...utils.permissions import role_required


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def resident_list(request):
    """
    list of residents
    """
    residents = User.objects.filter(role__role_name="ROLE_RESIDENT").select_related(
        "province", "district", "ward"
    )

    # Match address and get current room
    resident_data = []
    for resident in residents:
        address_parts = []
        if resident.detail_address:
            address_parts.append(resident.detail_address)
        if resident.ward:
            address_parts.append(resident.ward.ward_name)
        if resident.district:
            address_parts.append(resident.district.district_name)
        if resident.province:
            address_parts.append(resident.province.province_name)
        address = ", ".join(address_parts) if address_parts else _("Chưa có phòng")

        # Get the current room
        current_room = (
            RoomResident.objects.filter(user=resident, move_out_date__isnull=True)
            .select_related("room")
            .first()
        )
        room_id = current_room.room.room_id if current_room else _("Chưa có phòng")

        resident_data.append(
            {
                "user_id": resident.user_id,
                "full_name": resident.full_name,
                "email": resident.email,
                "phone": resident.phone,
                "address": address,
                "room_id": room_id,
                "history": RoomResident.objects.filter(user=resident).select_related(
                    "room"
                ),
            }
        )

    context = {
        "residents": resident_data,
        "form": ResidentRoomForm(),
    }
    return render(request, "manager/resident/resident_list.html", context)


@require_POST
@login_required
@csrf_protect
@role_required(UserRole.APARTMENT_MANAGER.value)
def assign_room(request, user_id):
    """
    Assign or transfer rooms to residents.
    """
    resident = get_object_or_404(User, pk=user_id, role__role_name="ROLE_RESIDENT")

    form = ResidentRoomForm(request.POST)
    form.resident = resident
    if form.is_valid():
        room = form.cleaned_data["room"]
        move_in_date = form.cleaned_data["move_in_date"]

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

        # Create notification: pass (Để lại sau)

        messages.success(
            request,
            _("Gán phòng thành công cho cư dân %(name)s.")
            % {"name": resident.full_name},
        )
    else:
        messages.error(request, _("Dữ liệu không hợp lệ. Vui lòng kiểm tra lại."))

    return redirect("resident_list")


@require_POST
@login_required
@csrf_protect
@role_required(UserRole.APARTMENT_MANAGER.value)
def leave_room(request, user_id):
    resident = get_object_or_404(User, pk=user_id, role__role_name="ROLE_RESIDENT")

    # Tìm xem cư dân có đang ở phòng nào không
    current_room_resident = RoomResident.objects.filter(
        user=resident, move_out_date__isnull=True
    ).first()

    if not current_room_resident:
        messages.error(request, _("Cư dân này hiện không ở trong phòng nào."))
        return redirect("resident_list")

    # Cập nhật ngày chuyển đi là hôm nay
    current_room_resident.move_out_date = timezone.now()

    # # nếu cư dân này là người cuối cùng rời phòng, cập nhật trạng thái phòng
    remaining = RoomResident.objects.filter(
        room=current_room_resident.room, move_out_date__isnull=True
    ).count()
    if remaining == 0:
        current_room_resident.room.status = RoomStatus.AVAILABLE.value
        current_room_resident.room.save()

    current_room_resident.save()

    # create notifications: pass (để lại sau)

    messages.success(
        request,
        _(f"Đã chuyển cư dân {resident.full_name} ra khỏi phòng thành công."),
    )
    return redirect("resident_list")
