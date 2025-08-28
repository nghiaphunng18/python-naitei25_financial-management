from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from ...models import Notification, User, Role
from ...constants import StringLength, NotificationStatus, UserRole


class NotificationModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(
            role_id=1, role_name=UserRole.RESIDENT.value, description="Resident role"
        )
        self.sender = User.objects.create(
            user_id="RES001",
            full_name="Nguyen Van A",
            email="a.nguyen@example.com",
            phone="0901234567",
            role=self.role,
            is_active=1,
        )
        self.receiver = User.objects.create(
            user_id="RES002",
            full_name="Nguyen Van B",
            email="b.nguyen@example.com",
            phone="0907654321",
            role=self.role,
            is_active=1,
        )
        self.notification = Notification.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            title="Thông báo mới",
            message="Bạn có hóa đơn mới cần thanh toán.",
            status=NotificationStatus.UNREAD.value,
        )

    def test_notification_creation(self):
        self.assertEqual(self.notification.sender, self.sender)
        self.assertEqual(self.notification.receiver, self.receiver)
        self.assertEqual(self.notification.title, "Thông báo mới")
        self.assertEqual(
            self.notification.message, "Bạn có hóa đơn mới cần thanh toán."
        )
        self.assertEqual(self.notification.status, NotificationStatus.UNREAD.value)
        self.assertIsNotNone(self.notification.created_at)

    def test_notification_str(self):
        self.assertEqual(str(self.notification), "Thông báo mới")

    def test_restrict_delete_sender(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa sender"""
        with self.assertRaises(IntegrityError):
            self.sender.delete()

    def test_receiver_nullable(self):
        notification = Notification.objects.create(
            sender=self.sender,
            title="Thông báo chung",
            message="Thông báo cho tất cả cư dân.",
            status=NotificationStatus.UNREAD.value,
        )
        self.assertIsNone(notification.receiver)
