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
        required=True,
    )
    move_in_date = forms.DateField(
        label=_("Ngày vào"),
        widget=forms.DateInput(
            attrs={"type": "date", "class": "w-full p-2 border rounded"}
        ),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.resident = kwargs.pop("resident", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get("room")
        move_in_date = cleaned_data.get("move_in_date")

        # Kiểm tra ngày vào không trong quá khứ
        if move_in_date and move_in_date < date.today():
            raise forms.ValidationError(_("Ngày vào không được là ngày trong quá khứ."))

        # Kiểm tra ngày vào so với ngày rời phòng trước (nếu có)
        if self.resident:
            last_stay = (
                RoomResident.objects.filter(user=self.resident)
                .order_by("-move_in_date")
                .first()
            )
            if (
                last_stay
                and last_stay.move_out_date
                and move_in_date
                and move_in_date
                <= last_stay.move_out_date.date()  # Chuyển datetime thành date
            ):
                raise forms.ValidationError(
                    _("Ngày vào phải sau ngày rời phòng trước đó.")
                )

        # Kiểm tra gán phòng
        if room and move_in_date:
            current_occupants = (
                room.residents.filter(  # Sửa từ roomresident_set thành residents
                    move_out_date__isnull=True
                ).count()
            )
            if current_occupants >= room.max_occupants:
                raise forms.ValidationError(
                    _("Phòng đã đầy, không thể gán thêm cư dân.")
                )
        else:
            raise forms.ValidationError(_("Vui lòng chọn cả phòng và ngày vào."))

        return cleaned_data
