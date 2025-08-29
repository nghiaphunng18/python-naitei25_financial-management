from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from ...models import DraftBill, Room
from ...constants import RoomStatus


class DraftBillModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            room_id="P101", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        self.draft_bill = DraftBill.objects.create(
            room=self.room,
            bill_month=timezone.now().date(),
            draft_type=DraftBill.DraftType.ELECTRIC_WATER,
            status=DraftBill.DraftStatus.DRAFT,
            total_amount=500000.00,
            details={"electricity": 300000, "water": 200000},
        )

    def test_draft_bill_creation(self):
        """Kiểm tra tạo DraftBill thành công"""
        self.assertEqual(self.draft_bill.room, self.room)
        self.assertEqual(self.draft_bill.draft_type, DraftBill.DraftType.ELECTRIC_WATER)
        self.assertEqual(self.draft_bill.status, DraftBill.DraftStatus.DRAFT)
        self.assertEqual(self.draft_bill.total_amount, 500000.00)
        self.assertEqual(
            self.draft_bill.details, {"electricity": 300000, "water": 200000}
        )
        self.assertIsNotNone(self.draft_bill.created_at)

    def test_draft_bill_str(self):
        """Kiểm tra phương thức __str__"""
        expected_str = f"Draft Bill for {self.room} - {self.draft_bill.bill_month.strftime('%Y-%m')} (Điện & Nước)"
        self.assertEqual(str(self.draft_bill), expected_str)

    def test_unique_together(self):
        """Kiểm tra ràng buộc unique_together"""
        with self.assertRaises(IntegrityError):
            DraftBill.objects.create(
                room=self.room,
                bill_month=timezone.now().date(),
                draft_type=DraftBill.DraftType.ELECTRIC_WATER,
                status=DraftBill.DraftStatus.DRAFT,
                total_amount=600000.00,
            )

    def test_cascade_delete_room(self):
        """Kiểm tra CASCADE khi xóa Room"""
        self.room.delete()
        self.assertFalse(
            DraftBill.objects.filter(
                draft_bill_id=self.draft_bill.draft_bill_id
            ).exists()
        )
