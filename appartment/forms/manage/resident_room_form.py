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

    def __init__(self, *args, **kwargs):
        self.resident = kwargs.pop("resident", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get("room")

        if not room:
            raise forms.ValidationError(_("Vui lòng chọn phòng."))

        # Kiểm tra số lượng cư dân hiện tại trong phòng
        current_occupants = room.residents.filter(move_out_date__isnull=True).count()
        if current_occupants >= room.max_occupants:
            raise forms.ValidationError(_("Phòng đã đầy, không thể gán thêm cư dân."))

        return cleaned_data
