from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from ...models import PaymentHistory, Bill, Room, User, Role
from ...constants import (
    StringLength,
    PaymentMethod,
    PaymentTransactionStatus,
    RoomStatus,
    UserRole,
    DecimalConfig,
    PaymentStatus,
)


class PaymentHistoryModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            room_id="P101", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        self.bill = Bill.objects.create(
            bill_month=timezone.now(),
            total_amount=100000.00,
            status=PaymentStatus.UNPAID.value,
            room=self.room,
        )
        self.role = Role.objects.create(
            role_id=1,
            role_name=UserRole.APARTMENT_MANAGER.value,
            description="Manager role",
        )
        self.user = User.objects.create(
            user_id="MAN001",
            full_name="Manager A",
            email="manager@example.com",
            phone="0901234567",
            role=self.role,
            is_active=1,
        )
        self.payment = PaymentHistory.objects.create(
            bill=self.bill,
            order_code=123456789,
            payment_date=timezone.now(),
            amount_paid=100000.00,
            payment_method=PaymentMethod.BANK_TRANSFER.value,
            processed_by=self.user,
            notes="Thanh toán qua ngân hàng",
            transaction_status=PaymentTransactionStatus.SUCCESS.value,
        )

    def test_payment_history_creation(self):
        self.assertEqual(self.payment.bill, self.bill)
        self.assertEqual(self.payment.order_code, 123456789)
        self.assertEqual(self.payment.amount_paid, 100000.00)
        self.assertEqual(self.payment.payment_method, PaymentMethod.BANK_TRANSFER.value)
        self.assertEqual(self.payment.processed_by, self.user)
        self.assertEqual(self.payment.notes, "Thanh toán qua ngân hàng")
        self.assertEqual(
            self.payment.transaction_status, PaymentTransactionStatus.SUCCESS.value
        )
        self.assertIsNotNone(self.payment.payment_date)

    def test_payment_history_str(self):
        self.assertEqual(
            str(self.payment),
            f"Payment {self.payment.payment_id} for Bill {self.bill.bill_id}",
        )

    def test_restrict_delete_bill(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa Bill"""
        with self.assertRaises(IntegrityError):
            self.bill.delete()

    def test_processed_by_nullable(self):
        """Kiểm tra processed_by có thể null"""
        payment = PaymentHistory.objects.create(
            bill=self.bill,
            amount_paid=50000.00,
            payment_method=PaymentMethod.CASH.value,
        )
        self.assertIsNone(payment.processed_by)
