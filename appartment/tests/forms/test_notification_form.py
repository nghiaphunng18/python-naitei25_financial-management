from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from ...forms.manage.notification_form import NotificationForm
from ...constants import UserRole


class NotificationFormTest(TestCase):
    def test_init_resident(self):
        """Kiểm tra khởi tạo form cho resident (không có receiver_type và send_all)"""
        form = NotificationForm(sender_role=UserRole.RESIDENT.value)
        self.assertNotIn("receiver_type", form.fields)
        self.assertNotIn("send_all", form.fields)
        self.assertIn("title", form.fields)
        self.assertIn("message", form.fields)

    def test_init_manager(self):
        """Kiểm tra khởi tạo form cho manager (có receiver_type và send_all)"""
        form = NotificationForm(sender_role=UserRole.APARTMENT_MANAGER.value)
        self.assertIn("receiver_type", form.fields)
        self.assertIn("send_all", form.fields)
        self.assertIn("title", form.fields)
        self.assertIn("message", form.fields)
        self.assertTrue(form.fields["receiver_type"].required)

    def test_init_admin(self):
        """Kiểm tra khởi tạo form cho admin (có receiver_type và send_all)"""
        form = NotificationForm(sender_role=UserRole.ADMIN.value)
        self.assertIn("receiver_type", form.fields)
        self.assertIn("send_all", form.fields)
        self.assertIn("message", form.fields)
        self.assertTrue(form.fields["receiver_type"].required)

    def test_valid_form_resident(self):
        """Kiểm tra form hợp lệ cho resident"""
        data = {
            "title": "Yêu cầu sửa chữa",
            "message": "Cần sửa ống nước phòng 101.",
        }
        form = NotificationForm(data=data, sender_role=UserRole.RESIDENT.value)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["title"], "Yêu cầu sửa chữa")
        self.assertEqual(form.cleaned_data["message"], "Cần sửa ống nước phòng 101.")

    def test_valid_form_manager(self):
        """Kiểm tra form hợp lệ cho manager"""
        data = {
            "receiver_type": "resident",
            "send_all": False,
            "title": "Thông báo bảo trì",
            "message": "Bảo trì tòa nhà ngày mai.",
        }
        form = NotificationForm(data=data, sender_role=UserRole.APARTMENT_MANAGER.value)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["receiver_type"], "resident")
        self.assertEqual(form.cleaned_data["send_all"], False)
        self.assertEqual(form.cleaned_data["title"], "Thông báo bảo trì")
        self.assertEqual(form.cleaned_data["message"], "Bảo trì tòa nhà ngày mai.")

    def test_valid_form_admin(self):
        """Kiểm tra form hợp lệ cho admin"""
        data = {
            "receiver_type": "manager",
            "send_all": True,
            "title": "Thông báo hệ thống",
            "message": "Hệ thống bảo trì ngày mai.",
        }
        form = NotificationForm(data=data, sender_role=UserRole.ADMIN.value)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["receiver_type"], "manager")
        self.assertEqual(form.cleaned_data["send_all"], True)
        self.assertEqual(form.cleaned_data["title"], "Thông báo hệ thống")
        self.assertEqual(form.cleaned_data["message"], "Hệ thống bảo trì ngày mai.")

    def test_invalid_form_resident_missing_title(self):
        """Kiểm tra form không hợp lệ cho resident khi thiếu title"""
        data = {
            "title": "",
            "message": "Cần sửa ống nước phòng 101.",
        }
        form = NotificationForm(data=data, sender_role=UserRole.RESIDENT.value)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertEqual(form.errors["title"], [_("This field is required.")])

    def test_invalid_form_resident_missing_message(self):
        """Kiểm tra form không hợp lệ cho resident khi thiếu message"""
        data = {
            "title": "Yêu cầu sửa chữa",
            "message": "",
        }
        form = NotificationForm(data=data, sender_role=UserRole.RESIDENT.value)
        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)
        self.assertEqual(form.errors["message"], [_("This field is required.")])

    def test_invalid_form_manager_missing_receiver_type(self):
        """Kiểm tra form không hợp lệ cho manager khi thiếu receiver_type"""
        data = {
            "receiver_type": "",
            "send_all": False,
            "title": "Thông báo bảo trì",
            "message": "Bảo trì tòa nhà ngày mai.",
        }
        form = NotificationForm(data=data, sender_role=UserRole.APARTMENT_MANAGER.value)
        self.assertFalse(form.is_valid())
        self.assertIn("receiver_type", form.errors)
        self.assertEqual(form.errors["receiver_type"], [_("This field is required.")])

    def test_invalid_form_manager_missing_title(self):
        """Kiểm tra form không hợp lệ cho manager khi thiếu title"""
        data = {
            "receiver_type": "resident",
            "send_all": False,
            "title": "",
            "message": "Bảo trì tòa nhà ngày mai.",
        }
        form = NotificationForm(data=data, sender_role=UserRole.APARTMENT_MANAGER.value)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertEqual(form.errors["title"], [_("This field is required.")])

    def test_invalid_form_admin_missing_receiver_type(self):
        """Kiểm tra form không hợp lệ cho admin khi thiếu receiver_type"""
        data = {
            "receiver_type": "",
            "send_all": False,
            "title": "Thông báo hệ thống",
            "message": "Hệ thống bảo trì ngày mai.",
        }
        form = NotificationForm(data=data, sender_role=UserRole.ADMIN.value)
        self.assertFalse(form.is_valid())
        self.assertIn("receiver_type", form.errors)
        self.assertEqual(form.errors["receiver_type"], [_("This field is required.")])

    def test_invalid_form_admin_missing_message(self):
        """Kiểm tra form không hợp lệ cho admin khi thiếu message"""
        data = {
            "receiver_type": "manager",
            "send_all": False,
            "title": "Thông báo hệ thống",
            "message": "",
        }
        form = NotificationForm(data=data, sender_role=UserRole.ADMIN.value)
        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)
        self.assertEqual(form.errors["message"], [_("This field is required.")])

    def test_clean_method(self):
        """Kiểm tra phương thức clean trả về cleaned_data đúng"""
        data = {
            "receiver_type": "resident",
            "send_all": True,
            "title": "Thông báo bảo trì",
            "message": "Bảo trì tòa nhà ngày mai.",
        }
        form = NotificationForm(data=data, sender_role=UserRole.APARTMENT_MANAGER.value)
        self.assertTrue(form.is_valid())
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data["receiver_type"], "resident")
        self.assertEqual(cleaned_data["send_all"], True)
        self.assertEqual(cleaned_data["title"], "Thông báo bảo trì")
        self.assertEqual(cleaned_data["message"], "Bảo trì tòa nhà ngày mai.")
