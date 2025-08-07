from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.utils.translation import gettext_lazy as _
from decimal import Decimal, InvalidOperation

from appartment.constants import UserRole
from appartment.forms.manager.rental_price_form import (
    RentalPriceCreateForm,
    RentalPriceUpdateForm,
)
from appartment.utils.permissions import role_required

from ...models import Room, RentalPrice


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def rental_price_create(request, room_id):
    try:
        room = Room.objects.get(room_id=room_id)
    except Room.DoesNotExist:
        messages.error(
            request, _("Phòng có ID %(room_id)s không tồn tại.") % {"room_id": room_id}
        )
        return redirect("room_detail", room_id=room_id)

    if request.method == "POST":
        form = RentalPriceCreateForm(request.POST)
        if form.is_valid():
            price = form.cleaned_data["price"]
            effective_date = form.cleaned_data["effective_date"]

            RentalPrice.objects.create(
                room=room,
                price=price,
                effective_date=effective_date,
            )
            messages.success(
                request,
                _('Thêm giá mới vào phòng "%(room_id)s" thành công!')
                % {"room_id": room_id},
            )
            return redirect("room_detail", room_id=room_id)
    else:
        form = RentalPriceCreateForm()

    return redirect("room_detail", room_id=room_id)


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def rental_price_update(request, rental_price_id):
    try:
        rental_price = RentalPrice.objects.get(rental_price_id=rental_price_id)
    except RentalPrice.DoesNotExist:
        messages.error(
            request,
            _("ID giá thuê %(rental_price_id)s không tồn tại.")
            % {"rental_price_id": rental_price_id},
        )
        return redirect("room_list")

    if request.method == "POST":

        form = RentalPriceUpdateForm(request.POST)
        if form.is_valid():
            rental_price.price = form.cleaned_data["price"]
            rental_price.effective_date = form.cleaned_data["effective_date"]
            rental_price.save()
            messages.success(request, _("Cập nhật giá thuê thành công."))
        else:
            messages.error(request, _("Dữ liệu không hợp lệ."))

        return redirect("room_detail", room_id=rental_price.room.room_id)

    return redirect("room_detail", room_id=rental_price.room.room_id)


@login_required
@role_required(UserRole.APARTMENT_MANAGER.value)
def rental_price_delete(request, rental_price_id):
    try:
        price = RentalPrice.objects.get(rental_price_id=rental_price_id)
    except RentalPrice.DoesNotExist:
        messages.error(
            request,
            _("Giá thuê ID %(rental_price_id)s không tồn tại.")
            % {"rental_price_id": rental_price_id},
        )
        return redirect("room_list")

    room_id = price.room.room_id

    if request.method == "POST":
        price.delete()
        messages.success(request, _("Đã xóa giá thuê phòng thành công."))
        return redirect("room_detail", room_id=room_id)

    messages.error(request, _("Yêu cầu không hợp lệ."))
    return redirect("room_detail", room_id=room_id)
