from django import forms
from django.utils.translation import gettext_lazy as _
from ...models import Room
from ...constants import RoomStatus, MIN_OCCUPANTS, MAX_OCCUPANTS


class CreateRoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["room_id", "area", "description", "status", "max_occupants"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Customize form fields with Tailwind classes
        self.fields["room_id"].widget.attrs.update(
            {
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập tên phòng (ví dụ: A101, B202)"),
            }
        )

        self.fields["area"].widget.attrs.update(
            {
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Diện tích (m²)"),
                "step": "0.01",
            }
        )

        self.fields["description"].widget.attrs.update(
            {
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Mô tả phòng (tùy chọn)"),
                "rows": 4,
            }
        )

        self.fields["status"].widget.attrs.update(
            {
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            }
        )

        self.fields["max_occupants"].widget.attrs.update(
            {
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                "min": str(MIN_OCCUPANTS),
            }
        )

        # Set field labels in Vietnamese
        self.fields["room_id"].label = _("Tên phòng")
        self.fields["area"].label = _("Diện tích (m²)")
        self.fields["description"].label = _("Mô tả")
        self.fields["status"].label = _("Trạng thái")
        self.fields["max_occupants"].label = _("Số người tối đa")

        # Set required fields
        self.fields["room_id"].required = True
        self.fields["max_occupants"].required = True

    def clean_room_id(self):
        room_id = self.cleaned_data["room_id"]
        if Room.objects.filter(room_id=room_id).exists():
            raise forms.ValidationError(
                _("Tên phòng này đã tồn tại. Vui lòng chọn tên khác.")
            )
        return room_id

    def clean_area(self):
        area = self.cleaned_data.get("area")
        if area is not None and area <= 0:
            raise forms.ValidationError(_("Diện tích phải lớn hơn 0."))
        return area

    def clean_max_occupants(self):
        max_occupants = self.cleaned_data["max_occupants"]
        if max_occupants < MIN_OCCUPANTS:
            raise forms.ValidationError(
                _("Số người tối thiểu phải ít nhất là %s.") % MIN_OCCUPANTS
            )
        if max_occupants > MAX_OCCUPANTS:
            raise forms.ValidationError(
                _("Số người tối đa không được vượt quá %s.") % MAX_OCCUPANTS
            )
        return max_occupants


class UpdateRoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["area", "description", "status", "max_occupants"]

    def __init__(self, *args, **kwargs):
        # Lấy số người đang ở hiện tại để validation
        self.current_occupants = kwargs.pop("current_occupants", 0)
        super().__init__(*args, **kwargs)

        # Customize form fields với Tailwind classes
        self.fields["area"].widget.attrs.update(
            {
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Diện tích (m²)"),
                "step": "0.01",
            }
        )

        self.fields["description"].widget.attrs.update(
            {
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Mô tả phòng (tùy chọn)"),
                "rows": 4,
            }
        )

        self.fields["status"].widget.attrs.update(
            {
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            }
        )

        self.fields["max_occupants"].widget.attrs.update(
            {
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                "min": str(MIN_OCCUPANTS),
            }
        )

        # Set field labels in Vietnamese
        self.fields["area"].label = _("Diện tích (m²)")
        self.fields["description"].label = _("Mô tả")
        self.fields["status"].label = _("Trạng thái")
        self.fields["max_occupants"].label = _("Số người tối đa")

        # Set required fields
        self.fields["max_occupants"].required = True

        # Thêm help text cho max_occupants
        if self.current_occupants > 0:
            self.fields["max_occupants"].help_text = _(
                "Hiện có %(current_occupants)s người đang ở. Số tối đa phải >= %(current_occupants)s"
            ) % {"current_occupants": self.current_occupants}

    def clean_area(self):
        area = self.cleaned_data.get("area")
        if area is not None and area <= 0:
            raise forms.ValidationError(_("Diện tích phải lớn hơn 0."))
        return area

    def clean_max_occupants(self):
        max_occupants = self.cleaned_data["max_occupants"]

        # Kiểm tra giá trị cơ bản
        if max_occupants < MIN_OCCUPANTS:
            raise forms.ValidationError(
                _("Số người tối đa phải ít nhất là %s.") % MIN_OCCUPANTS
            )

        if max_occupants > MAX_OCCUPANTS:
            raise forms.ValidationError(
                _("Số người tối đa không được vượt quá %s.") % MAX_OCCUPANTS
            )

        # Kiểm tra không được nhỏ hơn số người đang ở hiện tại
        if max_occupants < self.current_occupants:
            raise forms.ValidationError(
                _(
                    "Số người tối đa (%(max_occupants)s) không thể nhỏ hơn số người đang ở hiện tại (%(current_occupants)s). Vui lòng chọn ít nhất %(current_occupants)s người."
                )
                % {
                    "max_occupants": max_occupants,
                    "current_occupants": self.current_occupants,
                }
            )

        return max_occupants

    def clean_status(self):
        status = self.cleaned_data["status"]

        # Nếu có người ở mà đặt status là maintenance, cảnh báo
        if status == RoomStatus.MAINTENANCE and self.current_occupants > 0:
            # Không block nhưng có thể thêm warning message
            pass

        return status
