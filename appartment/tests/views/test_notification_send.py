from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages
from django.utils.translation import gettext_lazy as _

from ...models import Notification, Role, User
from ...constants import UserRole, NotificationStatus


class NotificationSendTest(TestCase):
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
        self.resident2 = User.objects.create(
            user_id="RES002",
            full_name="Nguyễn Văn B",
            email="resident2@example.com",
            phone="0901234568",
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

    def _get_messages(self, response):
        return list(get_messages(response.wsgi_request))

    def test_resident_send_notification_get(self):
        """Kiểm tra hiển thị form gửi thông báo cho resident"""
        self.client.force_login(self.resident)
        url = reverse("resident_send_notification")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "resident/notifications/send_notification.html"
        )
        self.assertIn("form", response.context)

    def test_resident_send_notification_post_valid(self):
        """Kiểm tra gửi thông báo hợp lệ cho resident"""
        self.client.force_login(self.resident)
        url = reverse("resident_send_notification")
        data = {
            "title": "Yêu cầu sửa chữa",
            "message": "Cần sửa ống nước phòng 101.",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("resident_notification_history"))
        messages = self._get_messages(response)
        self.assertEqual(str(messages[0]), _("Thông báo đã được gửi thành công."))
        notification = Notification.objects.get(title="Yêu cầu sửa chữa")
        self.assertEqual(notification.sender, self.resident)
        self.assertIsNone(notification.receiver)
        self.assertEqual(notification.message, "Cần sửa ống nước phòng 101.")
        self.assertEqual(notification.status, NotificationStatus.UNREAD.value)

    def test_resident_send_notification_post_invalid(self):
        """Kiểm tra gửi thông báo với form không hợp lệ cho resident"""
        self.client.force_login(self.resident)
        url = reverse("resident_send_notification")
        data = {
            "title": "",  # Title rỗng, không hợp lệ
            "message": "Cần sửa ống nước phòng 101.",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "resident/notifications/send_notification.html"
        )
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]), _("Form không hợp lệ. Vui lòng kiểm tra lại.")
        )
        self.assertFalse(
            Notification.objects.filter(message="Cần sửa ống nước phòng 101.").exists()
        )

    def test_manager_send_notification_get(self):
        """Kiểm tra hiển thị form gửi thông báo cho manager"""
        self.client.force_login(self.manager)
        url = reverse("manager_send_notification")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "manager/notifications/send_notification.html"
        )
        self.assertIn("form", response.context)

    def test_manager_send_notification_post_valid_send_all(self):
        """Kiểm tra gửi thông báo hợp lệ cho manager với send_all=True"""
        self.client.force_login(self.manager)
        url = reverse("manager_send_notification")
        data = {
            "receiver_type": "resident",
            "send_all": "on",
            "title": "Thông báo bảo trì",
            "message": "Bảo trì tòa nhà ngày mai.",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("manager_notification_history"))
        messages = self._get_messages(response)
        self.assertEqual(str(messages[0]), _("Thông báo đã được gửi thành công."))
        notifications = Notification.objects.filter(title="Thông báo bảo trì")
        self.assertEqual(notifications.count(), 2)  # Gửi tới cả 2 resident
        for notification in notifications:
            self.assertEqual(notification.sender, self.manager)
            self.assertIn(notification.receiver.user_id, ["RES001", "RES002"])
            self.assertEqual(notification.message, "Bảo trì tòa nhà ngày mai.")
            self.assertEqual(notification.status, NotificationStatus.UNREAD.value)

    def test_manager_send_notification_post_valid_selected_receivers(self):
        """Kiểm tra gửi thông báo hợp lệ cho manager với danh sách người nhận cụ thể"""
        self.client.force_login(self.manager)
        url = reverse("manager_send_notification")
        data = {
            "receiver_type": "resident",
            "receiver": ["RES001"],
            "title": "Thông báo gán phòng",
            "message": "Bạn được gán vào phòng 101.",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("manager_notification_history"))
        messages = self._get_messages(response)
        self.assertEqual(str(messages[0]), _("Thông báo đã được gửi thành công."))
        notification = Notification.objects.get(title="Thông báo gán phòng")
        self.assertEqual(notification.sender, self.manager)
        self.assertEqual(notification.receiver, self.resident)
        self.assertEqual(notification.message, "Bạn được gán vào phòng 101.")
        self.assertEqual(notification.status, NotificationStatus.UNREAD.value)

    def test_manager_send_notification_post_no_receivers(self):
        """Kiểm tra lỗi khi manager không chọn người nhận và không tích send_all"""
        self.client.force_login(self.manager)
        url = reverse("manager_send_notification")
        data = {
            "receiver_type": "resident",
            "title": "Thông báo lỗi",
            "message": "Không chọn người nhận.",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "manager/notifications/send_notification.html"
        )
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]),
            _("Vui lòng chọn ít nhất một người nhận hoặc tích gửi cho tất cả."),
        )
        self.assertFalse(Notification.objects.filter(title="Thông báo lỗi").exists())

    def test_manager_send_notification_post_invalid_form(self):
        """Kiểm tra lỗi khi form không hợp lệ cho manager"""
        self.client.force_login(self.manager)
        url = reverse("manager_send_notification")
        data = {
            "receiver_type": "resident",
            "title": "",  # Title rỗng, không hợp lệ
            "message": "Thông báo không hợp lệ.",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "manager/notifications/send_notification.html"
        )
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]), _("Form không hợp lệ. Vui lòng kiểm tra lại.")
        )
        self.assertFalse(
            Notification.objects.filter(message="Thông báo không hợp lệ.").exists()
        )

    def test_manager_send_notification_post_invalid_receiver(self):
        """Kiểm tra lỗi khi manager gửi tới người nhận không tồn tại"""
        self.client.force_login(self.manager)
        url = reverse("manager_send_notification")
        data = {
            "receiver_type": "resident",
            "receiver": ["INVALID_ID"],
            "title": "Thông báo lỗi",
            "message": "Người nhận không tồn tại.",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("manager_notification_history"))
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]), _("Người nhận với ID INVALID_ID không tồn tại.")
        )
        self.assertFalse(Notification.objects.filter(title="Thông báo lỗi").exists())

    def test_admin_send_notification_get(self):
        """Kiểm tra hiển thị form gửi thông báo cho admin"""
        self.client.force_login(self.admin)
        url = reverse("admin_send_notification")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/notifications/send_notification.html")
        self.assertIn("form", response.context)

    def test_admin_send_notification_post_valid_send_all(self):
        """Kiểm tra gửi thông báo hợp lệ cho admin với send_all=True"""
        self.client.force_login(self.admin)
        url = reverse("admin_send_notification")
        data = {
            "receiver_type": "manager",
            "send_all": "on",
            "title": "Thông báo hệ thống",
            "message": "Hệ thống bảo trì ngày mai.",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("admin_notification_history"))
        messages = self._get_messages(response)
        self.assertEqual(str(messages[0]), _("Thông báo đã được gửi thành công."))
        notifications = Notification.objects.filter(title="Thông báo hệ thống")
        self.assertEqual(notifications.count(), 1)  # Gửi tới 1 manager
        notification = notifications.first()
        self.assertEqual(notification.sender, self.admin)
        self.assertEqual(notification.receiver, self.manager)
        self.assertEqual(notification.message, "Hệ thống bảo trì ngày mai.")
        self.assertEqual(notification.status, NotificationStatus.UNREAD.value)

    def test_admin_send_notification_post_valid_selected_receivers(self):
        """Kiểm tra gửi thông báo hợp lệ cho admin với danh sách người nhận cụ thể"""
        self.client.force_login(self.admin)
        url = reverse("admin_send_notification")
        data = {
            "receiver_type": "resident",
            "receiver": ["RES001"],
            "title": "Thông báo gán phòng",
            "message": "Bạn được gán vào phòng 101.",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("admin_notification_history"))
        messages = self._get_messages(response)
        self.assertEqual(str(messages[0]), _("Thông báo đã được gửi thành công."))
        notification = Notification.objects.get(title="Thông báo gán phòng")
        self.assertEqual(notification.sender, self.admin)
        self.assertEqual(notification.receiver, self.resident)
        self.assertEqual(notification.message, "Bạn được gán vào phòng 101.")
        self.assertEqual(notification.status, NotificationStatus.UNREAD.value)

    def test_admin_send_notification_post_no_receivers(self):
        """Kiểm tra lỗi khi admin không chọn người nhận và không tích send_all"""
        self.client.force_login(self.admin)
        url = reverse("admin_send_notification")
        data = {
            "receiver_type": "resident",
            "title": "Thông báo lỗi",
            "message": "Không chọn người nhận.",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/notifications/send_notification.html")
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]),
            _("Vui lòng chọn ít nhất một người nhận hoặc tích gửi cho tất cả."),
        )
        self.assertFalse(Notification.objects.filter(title="Thông báo lỗi").exists())

    def test_admin_send_notification_post_invalid_form(self):
        """Kiểm tra lỗi khi form không hợp lệ cho admin"""
        self.client.force_login(self.admin)
        url = reverse("admin_send_notification")
        data = {
            "receiver_type": "resident",
            "title": "",  # Title rỗng, không hợp lệ
            "message": "Thông báo không hợp lệ.",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/notifications/send_notification.html")
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]), _("Form không hợp lệ. Vui lòng kiểm tra lại.")
        )
        self.assertFalse(
            Notification.objects.filter(message="Thông báo không hợp lệ.").exists()
        )

    def test_admin_send_notification_post_invalid_receiver(self):
        """Kiểm tra lỗi khi admin gửi tới người nhận không tồn tại"""
        self.client.force_login(self.admin)
        url = reverse("admin_send_notification")
        data = {
            "receiver_type": "resident",
            "receiver": ["INVALID_ID"],
            "title": "Thông báo lỗi",
            "message": "Người nhận không tồn tại.",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("admin_notification_history"))
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]), _("Người nhận với ID INVALID_ID không tồn tại.")
        )
        self.assertFalse(Notification.objects.filter(title="Thông báo lỗi").exists())

    def test_load_users_by_role_admin(self):
        """Kiểm tra AJAX load danh sách admin"""
        self.client.force_login(self.admin)
        url = reverse("load_users_by_role")
        response = self.client.post(url, {"receiver_type": "admin"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["users"], [{"id": "ADM001", "name": "Nguyễn Admin"}])

    def test_load_users_by_role_manager(self):
        """Kiểm tra AJAX load danh sách manager"""
        self.client.force_login(self.admin)
        url = reverse("load_users_by_role")
        response = self.client.post(url, {"receiver_type": "manager"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["users"], [{"id": "MAN001", "name": "Nguyễn Quản Lý"}])

    def test_load_users_by_role_resident(self):
        """Kiểm tra AJAX load danh sách resident"""
        self.client.force_login(self.admin)
        url = reverse("load_users_by_role")
        response = self.client.post(url, {"receiver_type": "resident"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data["users"],
            [
                {"id": "RES001", "name": "Nguyễn Văn A"},
                {"id": "RES002", "name": "Nguyễn Văn B"},
            ],
        )

    def test_load_users_by_role_invalid(self):
        """Kiểm tra AJAX load với receiver_type không hợp lệ"""
        self.client.force_login(self.admin)
        url = reverse("load_users_by_role")
        response = self.client.post(url, {"receiver_type": "invalid"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["users"], [])
