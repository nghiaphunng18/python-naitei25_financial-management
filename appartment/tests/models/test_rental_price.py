from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from ...models import RentalPrice, Room
from ...constants import RoomStatus, DecimalConfig


class RentalPriceModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            room_id="P101", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        self.rental_price = RentalPrice.objects.create(
            room=self.room, price=5000000.00, effective_date=timezone.now()
        )

    def test_rental_price_creation(self):
        self.assertEqual(self.rental_price.room, self.room)
        self.assertEqual(self.rental_price.price, 5000000.00)
        self.assertIsNotNone(self.rental_price.effective_date)

    def test_rental_price_str(self):
        self.assertEqual(str(self.rental_price), f"Price 5000000.00 for Room P101")

    def test_restrict_delete_room(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa Room"""
        with self.assertRaises(IntegrityError):
            self.room.delete()
