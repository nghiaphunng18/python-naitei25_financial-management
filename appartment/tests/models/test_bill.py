from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from ...models import Bill, Room
from ...constants import StringLength, PaymentStatus, RoomStatus, DecimalConfig


class BillModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            room_id="P101", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        self.bill = Bill.objects.create(
            bill_month=timezone.now(),
            electricity_amount=100.50,
            water_amount=50.25,
            additional_service_amount=200.00,
            total_amount=350.75,
            status=PaymentStatus.UNPAID.value,
            room=self.room,
            due_date=timezone.now() + timezone.timedelta(days=7),
        )

    def test_bill_creation(self):
        self.assertEqual(self.bill.electricity_amount, 100.50)
        self.assertEqual(self.bill.water_amount, 50.25)
        self.assertEqual(self.bill.additional_service_amount, 200.00)
        self.assertEqual(self.bill.total_amount, 350.75)
        self.assertEqual(self.bill.status, PaymentStatus.UNPAID.value)
        self.assertEqual(self.bill.room, self.room)
        self.assertIsNotNone(self.bill.created_at)
        self.assertIsNotNone(self.bill.due_date)

    def test_bill_str(self):
        self.assertEqual(str(self.bill), f"Bill {self.bill.bill_id} for Room P101")

    def test_restrict_delete_room(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa Room"""
        with self.assertRaises(IntegrityError):
            self.room.delete()

    def test_status_choices(self):
        """Kiểm tra giá trị status nằm trong choices"""
        bill = Bill(
            bill_month=timezone.now(),
            total_amount=1000.00,
            status="INVALID_STATUS",
            room=self.room,
        )
        with self.assertRaises(ValidationError):
            bill.full_clean()
