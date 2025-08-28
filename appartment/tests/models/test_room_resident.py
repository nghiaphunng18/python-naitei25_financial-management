from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from ...models import RoomResident, Room, User, Role
from ...constants import RoomStatus, UserRole


class RoomResidentModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(
            role_name=UserRole.RESIDENT.value, description="Resident role"
        )
        self.user = User.objects.create(
            user_id="RES001",
            full_name="Nguyen Van A",
            email="a.nguyen@example.com",
            phone="0901234567",
            role=self.role,
            is_active=1,
        )
        self.room = Room.objects.create(
            room_id="P101", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        self.room_resident = RoomResident.objects.create(
            user=self.user, room=self.room, move_in_date=timezone.now()
        )

    def test_room_resident_creation(self):
        self.assertEqual(self.room_resident.user, self.user)
        self.assertEqual(self.room_resident.room, self.room)
        self.assertIsNotNone(self.room_resident.move_in_date)
        self.assertIsNone(self.room_resident.move_out_date)

    def test_room_resident_str(self):
        self.assertEqual(str(self.room_resident), "Resident RES001 in Room P101")

    def test_restrict_delete_room(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa Room"""
        with self.assertRaises(IntegrityError):
            self.room.delete()

    def test_restrict_delete_user(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa User"""
        with self.assertRaises(IntegrityError):
            self.user.delete()
