from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from ...models import BillAdditionalService, Bill, AdditionalService, Room
from ...constants import StringLength, BillStatus, RoomStatus, ServiceType


class BillAdditionalServiceModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            room_id="P101", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        self.service = AdditionalService.objects.create(
            name="Wi-Fi", type=ServiceType.PER_ROOM.value, unit_price=100000.00
        )
        self.bill = Bill.objects.create(
            bill_month=timezone.now(),
            total_amount=100000.00,
            status=BillStatus.PENDING.value,
            room=self.room,
        )
        self.bill_service = BillAdditionalService.objects.create(
            bill=self.bill,
            additional_service=self.service,
            service_month=timezone.now(),
            status=BillStatus.PENDING.value,
            room=self.room,
        )

    def test_bill_additional_service_creation(self):
        self.assertEqual(self.bill_service.bill, self.bill)
        self.assertEqual(self.bill_service.additional_service, self.service)
        self.assertEqual(self.bill_service.status, BillStatus.PENDING.value)
        self.assertEqual(self.bill_service.room, self.room)
        self.assertIsNotNone(self.bill_service.service_month)

    def test_bill_additional_service_str(self):
        self.assertEqual(
            str(self.bill_service),
            f"Service {self.service.service_id} for Bill {self.bill.bill_id}",
        )

    def test_restrict_delete_service(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa AdditionalService"""
        with self.assertRaises(IntegrityError):
            self.service.delete()

    def test_restrict_delete_bill(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa Bill"""
        with self.assertRaises(IntegrityError):
            self.bill.delete()
