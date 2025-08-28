from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from ...models import Room
from ...constants import StringLength, RoomStatus


class RoomModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            room_id="P101",
            area=50.5,
            description="Phòng 2 người",
            status=RoomStatus.AVAILABLE.value,
            max_occupants=2,
        )

    def test_room_creation(self):
        self.assertEqual(self.room.room_id, "P101")
        self.assertEqual(self.room.area, 50.5)
        self.assertEqual(self.room.description, "Phòng 2 người")
        self.assertEqual(self.room.status, RoomStatus.AVAILABLE.value)
        self.assertEqual(self.room.max_occupants, 2)
        self.assertIsNotNone(self.room.created_at)

    def test_room_str(self):
        self.assertEqual(str(self.room), "P101")

    def test_room_id_unique(self):
        with self.assertRaises(IntegrityError):
            Room.objects.create(
                room_id="P101",
                area=60.0,
                status=RoomStatus.AVAILABLE.value,
                max_occupants=3,
            )

    def test_status_choices(self):
        room = Room(room_id="P102", status="INVALID_STATUS", max_occupants=2)
        with self.assertRaises(ValidationError):
            room.full_clean()
