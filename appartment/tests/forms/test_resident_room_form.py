from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from ...forms.manage.resident_room_form import (
    ResidentRoomForm,
)

from ...models import Room, RoomResident, User
from ...constants import RoomStatus


class ResidentRoomFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            user_id="RES001",
            full_name="Nguyen Van A",
            email="a.nguyen@example.com",
            phone="0901234567",
            role_id=1,
            is_active=True,
        )
        self.room = Room.objects.create(
            room_id="P101", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        self.room_full = Room.objects.create(
            room_id="P102", status=RoomStatus.OCCUPIED.value, max_occupants=1
        )
        RoomResident.objects.create(
            user=self.user,
            room=self.room_full,
            move_in_date="2025-01-01",
            move_out_date=None,
        )

    def test_form_fields(self):
        form = ResidentRoomForm()
        self.assertIn("room", form.fields)
        self.assertEqual(form.fields["room"].label, _("Phòng"))
        self.assertIsNone(form.fields["room"].empty_label)
        self.assertEqual(form.fields["room"].required, True)
        self.assertEqual(
            form.fields["room"].widget.attrs, {"class": "w-full p-2 border rounded"}
        )

    def test_form_queryset(self):
        form = ResidentRoomForm()
        rooms = form.fields["room"].queryset
        self.assertEqual(rooms.count(), 2)
        self.assertTrue(any(r.room_id == "P101" for r in rooms))
        self.assertTrue(any(r.room_id == "P102" for r in rooms))

    def test_valid_form(self):
        data = {"room": self.room.id}
        form = ResidentRoomForm(data, resident=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_form_no_room(self):
        data = {"room": ""}
        form = ResidentRoomForm(data, resident=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn(_("Vui lòng chọn phòng."), form.errors["room"])

    def test_invalid_form_full_room(self):
        data = {"room": self.room_full.id}
        form = ResidentRoomForm(data, resident=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn(
            _("Phòng đã đầy, không thể gán thêm cư dân."), form.errors["__all__"]
        )
