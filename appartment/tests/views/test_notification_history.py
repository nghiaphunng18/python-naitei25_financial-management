from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages
from django.utils.translation import gettext_lazy as _

from ...models import Notification, Role, User
from ...constants import UserRole, NotificationStatus, DEFAULT_PAGE_SIZE
from ...views.notification_history import (
    notification_history,
    resident_notification_history,
    manager_notification_history,
    admin_notification_history,
    mark_notification_read,
)
from ...utils.notification_utils import filter_notifications


class NotificationHistoryTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Tạo Role
        self.resident_role = Role.objects.create(
            role_id=1, role_name=UserRole.RESIDENT.value, description="Resident role"
        )
        self.manager_role = Role.objects.create(
            role_id=2,
            role_name=UserRole.APARTMENT_MANAGER.value,
            description="Manager role",
        )
        self.admin_role = Role.objects.create(
            role_id=3, role_name=UserRole.ADMIN.value, description="Admin role"
        )

        # Tạo User
        self.resident = User.objects.create(
            user_id="RES001",
            full_name="Nguyễn Văn A",
            email="resident@example.com",
            phone="0901234567",
            role_id=1,
            is_active=True,
        )
        self.manager = User.objects.create(
            user_id="MAN001",
            full_name="Nguyễn Quản Lý",
            email="manager@example.com",
            phone="0907654321",
            role_id=2,
            is_active=True,
        )
        self.admin = User.objects.create(
            user_id="ADM001",
            full_name="Nguyễn Admin",
            email="admin@example.com",
            phone="0909876543",
            role_id=3,
            is_active=True,
        )

        # Tạo Notification
        self.notification_to_resident = Notification.objects.create(
            sender=self.manager,
            receiver=self.resident,
            title="Gán phòng mới",
            message="Bạn đã được gán vào phòng 101.",
            status=NotificationStatus.UNREAD.value,
            created_at=timezone.now(),
        )
        self.notification_by_resident = Notification.objects.create(
            sender=self.resident,
            receiver=None,
            title="Yêu cầu sửa chữa",
            message="Cần sửa ống nước phòng 101.",
            status=NotificationStatus.UNREAD.value,
            created_at=timezone.now(),
        )
        self.notification_by_admin = Notification.objects.create(
            sender=self.admin,
            receiver=self.manager,
            title="Thông báo hệ thống",
            message="Hệ thống bảo trì ngày mai.",
            status=NotificationStatus.READ.value,
            created_at=timezone.now(),
        )

    def _get_messages(self, response):
        return list(get_messages(response.wsgi_request))

    def test_resident_notification_history_access(self):
        """Kiểm tra resident truy cập lịch sử thông báo"""
        self.client.force_login(self.resident)
        url = reverse("resident_notification_history")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "resident/notifications/history_notifications.html"
        )
        self.assertIn("notifications", response.context)
        self.assertIn("notifications_with_status", response.context)
        self.assertEqual(response.context["filter_type"], "all")

    def test_resident_notification_history_filter_to_me(self):
        """Kiểm tra lọc thông báo 'to_me' cho resident"""
        self.client.force_login(self.resident)
        url = reverse("resident_notification_history") + "?filter_type=to_me"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        notifications = response.context["notifications"].object_list
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0], self.notification_to_resident)

    def test_resident_notification_history_filter_by_me(self):
        """Kiểm tra lọc thông báo 'by_me' cho resident"""
        self.client.force_login(self.resident)
        url = reverse("resident_notification_history") + "?filter_type=by_me"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        notifications = response.context["notifications"].object_list
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0], self.notification_by_resident)

    def test_manager_notification_history_access(self):
        """Kiểm tra manager truy cập lịch sử thông báo"""
        self.client.force_login(self.manager)
        url = reverse("manager_notification_history")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "manager/notifications/history_notifications.html"
        )
        self.assertIn("notifications", response.context)
        self.assertIn("notifications_with_status", response.context)

    def test_manager_notification_history_filter_from_resident(self):
        """Kiểm tra lọc thông báo 'from_resident' cho manager"""
        self.client.force_login(self.manager)
        url = reverse("manager_notification_history") + "?filter_type=from_resident"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        notifications = response.context["notifications"].object_list
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0], self.notification_by_resident)

    def test_admin_notification_history_access(self):
        """Kiểm tra admin truy cập lịch sử thông báo"""
        self.client.force_login(self.admin)
        url = reverse("admin_notification_history")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "admin/notifications/history_notifications.html"
        )
        self.assertIn("notifications", response.context)
        self.assertIn("notifications_with_status", response.context)

    def test_admin_notification_history_filter_to_admin(self):
        """Kiểm tra lọc thông báo 'to_admin' cho admin"""
        self.client.force_login(self.admin)
        url = reverse("admin_notification_history") + "?filter_type=to_admin"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        notifications = response.context["notifications"].object_list
        self.assertEqual(
            len(notifications), 0
        )  # Không có thông báo to_admin trong dữ liệu mẫu

    def test_mark_notification_read_success(self):
        """Kiểm tra đánh dấu thông báo là đã đọc (resident có quyền)"""
        self.client.force_login(self.resident)
        url = reverse(
            "mark_notification_read",
            kwargs={"notification_id": self.notification_to_resident.notification_id},
        )
        response = self.client.post(url, {"csrfmiddlewaretoken": "testtoken"})
        self.assertRedirects(response, reverse("resident_notification_history"))
        self.notification_to_resident.refresh_from_db()
        self.assertEqual(
            self.notification_to_resident.status, NotificationStatus.READ.value
        )
        messages = self._get_messages(response)
        self.assertEqual(str(messages[0]), _("Thông báo đã được đánh dấu là đã đọc."))

    def test_mark_notification_read_no_permission(self):
        """Kiểm tra đánh dấu thông báo khi không có quyền"""
        self.client.force_login(self.resident)
        url = reverse(
            "mark_notification_read",
            kwargs={"notification_id": self.notification_by_admin.notification_id},
        )
        response = self.client.post(url, {"csrfmiddlewaretoken": "testtoken"})
        self.assertRedirects(response, reverse("resident_notification_history"))
        messages = self._get_messages(response)
        self.assertEqual(str(messages[0]), _("Bạn không có quyền xem thông báo này."))

    def test_filter_notifications_by_month(self):
        """Kiểm tra lọc thông báo theo tháng"""
        self.client.force_login(self.resident)
        url = "/?filter_month=2025-08"
        response = self.client.get(url, {"filter_month": "2025-08"})
        request = response.wsgi_request
        notifications = Notification.objects.filter(receiver=self.resident)
        context = filter_notifications(request, notifications)
        self.assertEqual(len(context["notifications"].object_list), 1)
        self.assertEqual(context["filter_month"], "2025-08")

    def test_filter_notifications_by_date_invalid(self):
        """Kiểm tra lọc thông báo với ngày không hợp lệ"""
        self.client.force_login(self.resident)
        url = "/?filter_date=invalid-date"
        response = self.client.get(url, {"filter_date": "invalid-date"})
        request = response.wsgi_request
        notifications = Notification.objects.filter(receiver=self.resident)
        context = filter_notifications(request, notifications)
        self.assertEqual(len(context["notifications"].object_list), 0)
        messages = self._get_messages(response)
        self.assertEqual(str(messages[0]), _("Định dạng ngày không hợp lệ."))

    def test_filter_notifications_search_query(self):
        """Kiểm tra tìm kiếm thông báo"""
        self.client.force_login(self.resident)
        url = "/?search_query=phòng 101"
        response = self.client.get(url, {"search_query": "phòng 101"})
        request = response.wsgi_request
        notifications = Notification.objects.filter(receiver=self.resident)
        context = filter_notifications(request, notifications)
        self.assertEqual(len(context["notifications"].object_list), 1)
        self.assertEqual(
            context["notifications"].object_list[0], self.notification_to_resident
        )

    def test_filter_notifications_sort_oldest(self):
        """Kiểm tra sắp xếp thông báo theo thứ tự cũ nhất"""
        self.client.force_login(self.resident)
        url = "/?sort_by=oldest"
        response = self.client.get(url, {"sort_by": "oldest"})
        request = response.wsgi_request
        notifications = Notification.objects.filter(receiver=self.resident)
        context = filter_notifications(request, notifications)
        self.assertEqual(context["sort_by"], "oldest")
        self.assertEqual(
            context["notifications"].object_list[0], self.notification_to_resident
        )
