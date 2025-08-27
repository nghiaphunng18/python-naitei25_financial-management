from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _

from appartment.constants import UserRole, RoomStatus
from appartment.models.rental_prices import RentalPrice
from ...forms.manager.room_forms import CreateRoomForm, UpdateRoomForm
from ...models import Room, RoomResident
from ...utils.permissions import role_required, staff_required
from ...forms.manager.rental_price_form import RentalPriceCreateForm


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
                    _("Có lỗi xảy ra khi tạo phòng: %(error)s")
                    % {"error": str(e)},
                )
        else:
            # Form có lỗi validation
            messages.error(
                request, _("Vui lòng kiểm tra lại thông tin đã nhập.")
            )
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

    rental_prices = RentalPrice.objects.filter(room=room).order_by(
        "-effective_date"
    )

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

    rental_price_form = RentalPriceCreateForm()
    context = {
        "room": room,
        "current_residents": current_residents,
        "past_residents": past_residents,
        "current_occupants_count": current_occupants_count,
        "total_residents_ever": total_residents_ever,
        "occupancy_rate": round(occupancy_rate, 1),
        "available_spots": room.max_occupants - current_occupants_count,
        "page_title": _("Chi tiết phòng %(room_id)s")
        % {"room_id": room.room_id},
        "rental_prices": rental_prices,
        "rental_price_form": rental_price_form,
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
                    _(
                        'Thông tin phòng "%(room_id)s" đã được cập nhật thành công!'
                    )
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
            messages.error(
                request, _("Vui lòng kiểm tra lại thông tin đã nhập.")
            )
    else:
        # GET request - hiển thị form với dữ liệu hiện tại
        form = UpdateRoomForm(
            instance=room, current_occupants=current_occupants
        )

    context = {
        "form": form,
        "room": room,
        "current_occupants": current_occupants,
        "page_title": _("Chỉnh sửa phòng %(room_id)s")
        % {"room_id": room.room_id},
    }

    return render(request, "manager/rooms/update_room.html", context)


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def room_list(request):
    """
    View để hiển thị danh sách phòng với thông tin số người ở và filter
    """
    # Lấy parameters từ URL
    status_filter = request.GET.get("status", "")
    occupancy_filter = request.GET.get("occupancy", "")
    area_filter = request.GET.get("area", "")
    max_occupants_filter = request.GET.get("max_occupants", "")

    # Base queryset
    rooms = Room.objects.all().order_by("-created_at")

    # Apply filters
    if status_filter:
        rooms = rooms.filter(status=status_filter)

    if area_filter:
        if area_filter == "small":  # < 20m²
            rooms = rooms.filter(area__lt=20)
        elif area_filter == "medium":  # 20-50m²
            rooms = rooms.filter(area__gte=20, area__lte=50)
        elif area_filter == "large":  # > 50m²
            rooms = rooms.filter(area__gt=50)

    if max_occupants_filter:
        if max_occupants_filter == "small":  # 1-2 người
            rooms = rooms.filter(max_occupants__lte=2)
        elif max_occupants_filter == "medium":  # 3-5 người
            rooms = rooms.filter(max_occupants__gte=3, max_occupants__lte=5)
        elif max_occupants_filter == "large":  # > 5 người
            rooms = rooms.filter(max_occupants__gt=5)

    # Cập nhật trạng thái phòng và thêm thông tin số người ở cho mỗi phòng
    rooms_with_occupants = []
    for room in rooms:
        current_occupants = RoomResident.objects.filter(
            room=room, move_out_date__isnull=True
        ).count()

        # Tự động cập nhật trạng thái phòng (chỉ với available/occupied)
        should_update_status = False
        if current_occupants == 0 and room.status == "occupied":
            room.status = "available"
            should_update_status = True
        elif current_occupants > 0 and room.status == "available":
            room.status = "occupied"
            should_update_status = True

        # Lưu thay đổi nếu cần (giữ nguyên maintenance và unavailable)
        if should_update_status:
            room.save(update_fields=["status"])

        occupancy_rate = (
            (current_occupants / room.max_occupants * 100)
            if room.max_occupants > 0
            else 0
        )

        room_data = {
            "room": room,
            "current_occupants": current_occupants,
            "occupancy_rate": occupancy_rate,
        }

        # Apply occupancy filter
        if occupancy_filter:
            if occupancy_filter == "empty" and current_occupants > 0:
                continue
            elif occupancy_filter == "partial" and (
                current_occupants == 0
                or current_occupants == room.max_occupants
            ):
                continue
            elif (
                occupancy_filter == "full"
                and current_occupants < room.max_occupants
            ):
                continue

        rooms_with_occupants.append(room_data)

    # AJAX request - return JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(
            request,
            "manager/rooms/room_cards.html",
            {
                "rooms_with_occupants": rooms_with_occupants,
            },
        )

    # Regular request - return full page
    context = {
        "rooms_with_occupants": rooms_with_occupants,
        "page_title": _("Danh sách phòng"),
        "total_rooms": len(rooms_with_occupants),
        "room_status_choices": RoomStatus.choices(),
        # Filter values for maintaining state
        "current_filters": {
            "status": status_filter,
            "occupancy": occupancy_filter,
            "area": area_filter,
            "max_occupants": max_occupants_filter,
        },
    }

    return render(request, "manager/rooms/room_list.html", context)
