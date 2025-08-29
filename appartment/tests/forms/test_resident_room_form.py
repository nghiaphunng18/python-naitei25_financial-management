from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

from ...models import Room, RoomResident, User, Role
from ...forms.manage.resident_room_form import ResidentRoomForm
from ...constants import RoomStatus, UserRole


class ResidentRoomFormTest(TestCase):
    def setUp(self):
        # Tạo Role
        self.resident_role = Role.objects.create(
            role_id=1, role_name=UserRole.RESIDENT.value, description="Resident role"
        )

        # Tạo User
        self.resident = User.objects.create(
            user_id="RES001",
            full_name="Nguyễn Văn A",
            email="a.nguyen@example.com",
            phone="0901234567",
            role_id=1,
            is_active=True,
        )
        self.another_resident = User.objects.create(
            user_id="RES002",
            full_name="Nguyễn Văn B",
            email="b.nguyen@example.com",
            phone="0907654321",
            role_id=1,
            is_active=True,
        )

        # Tạo Room
        self.room_available = Room.objects.create(
            room_id="101", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        self.room_occupied = Room.objects.create(
            room_id="102", status=RoomStatus.OCCUPIED.value, max_occupants=2
        )
        self.room_maintenance = Room.objects.create(
            room_id="103", status=RoomStatus.MAINTENANCE.value, max_occupants=2
        )

    def test_form_initialization_without_resident(self):
        """Kiểm tra khởi tạo form không có resident"""
        form = ResidentRoomForm()
        self.assertTrue(form.fields["room"].required)
        self.assertEqual(form.fields["room"].label, _("Phòng"))
        self.assertEqual(form.fields["room"].empty_label, None)
        self.assertEqual(
            form.fields["room"].widget.attrs["class"], "w-full p-2 border rounded"
        )
        # Kiểm tra queryset chỉ chứa phòng AVAILABLE và OCCUPIED
        expected_rooms = Room.objects.filter(
            status__in=[RoomStatus.AVAILABLE.value, RoomStatus.OCCUPIED.value]
        ).values_list("room_id", flat=True)
        form_rooms = form.fields["room"].queryset.values_list("room_id", flat=True)
        self.assertEqual(list(form_rooms), list(expected_rooms))

    def test_form_initialization_with_resident(self):
        """Kiểm tra khởi tạo form với resident"""
        form = ResidentRoomForm(resident=self.resident)
        self.assertEqual(form.resident, self.resident)
        self.assertTrue(form.fields["room"].required)
        # Kiểm tra queryset phòng
        expected_rooms = Room.objects.filter(
            status__in=[RoomStatus.AVAILABLE.value, RoomStatus.OCCUPIED.value]
        ).values_list("room_id", flat=True)
        form_rooms = form.fields["room"].queryset.values_list("room_id", flat=True)
        self.assertEqual(list(form_rooms), list(expected_rooms))

    def test_valid_form_submission(self):
        """Kiểm tra form hợp lệ khi chọn phòng hợp lệ"""
        data = {"room": self.room_available.room_id}
        form = ResidentRoomForm(data, resident=self.resident)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["room"], self.room_available)

    def test_form_no_room_selected(self):
        """Kiểm tra form không hợp lệ khi không chọn phòng"""
        data = {}
        form = ResidentRoomForm(data, resident=self.resident)
        self.assertFalse(form.is_valid())
        self.assertIn("room", form.errors)
        self.assertEqual(form.errors["room"], [_("Trường này là bắt buộc.")])

    def test_form_room_full(self):
        """Kiểm tra form khi phòng đã đầy"""
        # Thêm 2 cư dân vào phòng để đạt max_occupants
        RoomResident.objects.create(
            user=self.resident, room=self.room_occupied, move_in_date=timezone.now()
        )
        RoomResident.objects.create(
            user=self.another_resident,
            room=self.room_occupied,
            move_in_date=timezone.now(),
        )

        data = {"room": self.room_occupied.room_id}
        form = ResidentRoomForm(data, resident=self.resident)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertEqual(
            form.errors["__all__"], [_("Phòng đã đầy, không thể gán thêm cư dân.")]
        )

    def test_form_room_maintenance_not_in_queryset(self):
        """Kiểm tra phòng MAINTENANCE không xuất hiện trong queryset"""
        form = ResidentRoomForm(resident=self.resident)
        room_ids = form.fields["room"].queryset.values_list("room_id", flat=True)
        self.assertNotIn(self.room_maintenance.room_id, room_ids)

    def test_clean_method_no_room(self):
        """Kiểm tra phương thức clean khi không có phòng"""
        data = {"room": ""}
        form = ResidentRoomForm(data, resident=self.resident)
        self.assertFalse(form.is_valid())
        self.assertIn("room", form.errors)
        self.assertEqual(form.errors["room"], [_("Trường này là bắt buộc.")])
