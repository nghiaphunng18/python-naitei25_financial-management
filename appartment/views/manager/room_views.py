from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _

from appartment.constants import UserRole
from ...forms.manager.room_forms import CreateRoomForm, UpdateRoomForm
from ...models import Room, RoomResident
from ...utils.permissions import role_required, staff_required


@login_required
@require_http_methods(["GET", "POST"])
@role_required(UserRole.APARTMENT_MANAGER.value)
def create_room(request):
    """
    View để tạo phòng mới - chỉ dành cho manager (is_staff=True)
    """
    if request.method == "POST":
        form = CreateRoomForm(request.POST)

        if form.is_valid():
            try:
                # Lưu room mới
                room = form.save()
                messages.success(
                    request,
                    _('Phòng "%(room_id)s" đã được tạo thành công!')
                    % {"room_id": room.room_id},
                )

                # Reset form để có thể tạo phòng mới tiếp
                form = CreateRoomForm()

            except Exception as e:
                messages.error(
                    request,
                    _("Có lỗi xảy ra khi tạo phòng: %(error)s") % {"error": str(e)},
                )
        else:
            # Form có lỗi validation
            messages.error(request, _("Vui lòng kiểm tra lại thông tin đã nhập."))
    else:
        # GET request - hiển thị form trống
        form = CreateRoomForm()

    context = {
        "form": form,
        "page_title": _("Tạo phòng mới"),
    }

    return render(request, "manager/rooms/create_room.html", context)


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def room_detail(request, room_id):
    """
    View hiển thị chi tiết phòng - chỉ dành cho manager
    """
    # Lấy thông tin phòng
    room = get_object_or_404(Room, room_id=room_id)

    # Lấy danh sách người đang ở hiện tại (move_out_date = NULL)
    current_residents = (
        RoomResident.objects.filter(room=room, move_out_date__isnull=True)
        .select_related("user")
        .order_by("-move_in_date")
    )

    # Lấy lịch sử người ở (đã move out)
    past_residents = (
        RoomResident.objects.filter(room=room, move_out_date__isnull=False)
        .select_related("user")
        .order_by("-move_out_date")
    )

    # Tính số liệu thống kê
    current_occupants_count = current_residents.count()
    total_residents_ever = RoomResident.objects.filter(room=room).count()
    occupancy_rate = (
        (current_occupants_count / room.max_occupants * 100)
        if room.max_occupants > 0
        else 0
    )

    context = {
        "room": room,
        "current_residents": current_residents,
        "past_residents": past_residents,
        "current_occupants_count": current_occupants_count,
        "total_residents_ever": total_residents_ever,
        "occupancy_rate": round(occupancy_rate, 1),
        "available_spots": room.max_occupants - current_occupants_count,
        "page_title": _("Chi tiết phòng %(room_id)s") % {"room_id": room.room_id},
    }

    return render(request, "manager/rooms/room_detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
@role_required(UserRole.APARTMENT_MANAGER.value)
def room_update(request, room_id):
    """
    View cập nhật thông tin phòng - chỉ dành cho manager
    """
    # Lấy thông tin phòng
    room = get_object_or_404(Room, room_id=room_id)

    # Đếm số người đang ở hiện tại
    current_occupants = RoomResident.objects.filter(
        room=room, move_out_date__isnull=True
    ).count()

    if request.method == "POST":
        form = UpdateRoomForm(
            request.POST, instance=room, current_occupants=current_occupants
        )

        if form.is_valid():
            try:
                # Lưu thông tin cập nhật
                updated_room = form.save()
                messages.success(
                    request,
                    _('Thông tin phòng "%(room_id)s" đã được cập nhật thành công!')
                    % {"room_id": updated_room.room_id},
                )

                # Redirect về trang chi tiết
                return redirect("room_detail", room_id=room.room_id)

            except Exception as e:
                messages.error(
                    request,
                    _("Có lỗi xảy ra khi cập nhật phòng: %(error)s")
                    % {"error": str(e)},
                )
        else:
            # Form có lỗi validation
            messages.error(request, _("Vui lòng kiểm tra lại thông tin đã nhập."))
    else:
        # GET request - hiển thị form với dữ liệu hiện tại
        form = UpdateRoomForm(instance=room, current_occupants=current_occupants)

    context = {
        "form": form,
        "room": room,
        "current_occupants": current_occupants,
        "page_title": _("Chỉnh sửa phòng %(room_id)s") % {"room_id": room.room_id},
    }

    return render(request, "manager/rooms/update_room.html", context)


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def room_list(request):
    """
    View để hiển thị danh sách phòng với thông tin số người ở
    """
    # Lấy tất cả phòng với thông tin số người ở hiện tại
    rooms = Room.objects.all().order_by("-created_at")

    # Thêm thông tin số người ở cho mỗi phòng
    rooms_with_occupants = []
    for room in rooms:
        current_occupants = RoomResident.objects.filter(
            room=room, move_out_date__isnull=True
        ).count()

        room_data = {
            "room": room,
            "current_occupants": current_occupants,
            "occupancy_rate": (
                (current_occupants / room.max_occupants * 100)
                if room.max_occupants > 0
                else 0
            ),
        }
        rooms_with_occupants.append(room_data)

    context = {
        "rooms_with_occupants": rooms_with_occupants,
        "page_title": _("Danh sách phòng"),
    }

    return render(request, "manager/rooms/room_list.html", context)
