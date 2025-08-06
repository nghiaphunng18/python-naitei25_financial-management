from datetime import date

from django import forms
from django.utils.translation import gettext_lazy as _

from ...models import Room, RoomResident
from ...constants import RoomStatus


class ResidentRoomForm(forms.Form):
    room = forms.ModelChoiceField(
        queryset=Room.objects.filter(
            status__in=[RoomStatus.AVAILABLE.value, RoomStatus.OCCUPIED.value]
        ),
        label=_("Phòng"),
        empty_label=None,
        widget=forms.Select(attrs={"class": "w-full p-2 border rounded"}),
        required=False,
    )
    move_in_date = forms.DateField(
        label=_("Ngày vào"),
        widget=forms.DateInput(
            attrs={"type": "date", "class": "w-full p-2 border rounded"}
        ),
        required=False,
    )
    move_out_date = forms.DateField(
        label=_("Ngày rời"),
        widget=forms.DateInput(
            attrs={"type": "date", "class": "w-full p-2 border rounded"}
        ),
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get("room")
        move_in_date = cleaned_data.get("move_in_date")
        move_out_date = cleaned_data.get("move_out_date")

        # ngày chuyển vào không trong quá khứ
        if move_in_date and move_in_date < date.today():
            raise forms.ValidationError(_("Ngày vào không được là ngày trong quá khứ."))

        # ngày chuyển vào >= ngày rời phòng trước (nếu có)
        resident = getattr(self, "resident", None)
        if resident:
            last_stay = (
                RoomResident.objects.filter(user=resident)
                .order_by("-move_in_date")
                .first()
            )
            if (
                last_stay
                and last_stay.move_out_date
                and move_in_date
                and move_in_date <= last_stay.move_out_date
            ):
                raise forms.ValidationError(
                    _("Ngày vào phải sau ngày rời phòng trước đó.")
                )

        # Check for room assign
        if room or move_in_date:
            if not (room and move_in_date):
                raise forms.ValidationError(_("Vui lòng chọn cả phòng và ngày vào."))
            current_occupants = room.roomresident_set.filter(
                move_out_date__isnull=True
            ).count()
            if current_occupants >= room.max_occupants:
                raise forms.ValidationError(
                    _("Phòng đã đầy, không thể gán thêm cư dân.")
                )
        # Check for room leaving
        elif move_out_date:
            if not move_out_date:
                raise forms.ValidationError(_("Vui lòng chọn ngày rời."))
        else:
            raise forms.ValidationError(_("Vui lòng cung cấp thông tin hợp lệ."))

        return cleaned_data
