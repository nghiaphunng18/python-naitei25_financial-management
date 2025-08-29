from django.test import TestCase
from django import forms
from django.utils.translation import gettext_lazy as _
from ...models import User, Role
from ...forms.auth_forms import LoginForm


class LoginFormTest(TestCase):
    def setUp(self):
        # Tạo role trước
        self.role = Role.objects.create(
            role_name="Test Role", description="Role for testing"
        )

        # Tạo test user active
        self.user_active = User.objects.create_user(
            user_id="active_user",
            email="active@example.com",
            password="password123",
            full_name="Active User",
            phone="0123456789",
            role=self.role,
            is_active=1,  # IntegerField, not Boolean
        )

        # Tạo test user inactive
        self.user_inactive = User.objects.create_user(
            user_id="inactive_user",
            email="inactive@example.com",
            password="password123",
            full_name="Inactive User",
            phone="0123456789",
            role=self.role,
            is_active=0,  # Inactive
        )

    def test_form_fields(self):
        """Kiểm tra attributes của các fields"""
        form = LoginForm()
        # Kiểm tra email field
        self.assertEqual(form.fields["email"].label, _("Email"))
        self.assertIsInstance(form.fields["email"].widget, forms.EmailInput)
        # Kiểm tra password field
        self.assertEqual(form.fields["password"].label, _("Mật khẩu"))
        self.assertIsInstance(
            form.fields["password"].widget, forms.PasswordInput
        )
        # Kiểm tra remember_me field
        self.assertEqual(
            form.fields["remember_me"].label, _("Ghi nhớ đăng nhập")
        )
        self.assertIsInstance(
            form.fields["remember_me"].widget, forms.CheckboxInput
        )

    def test_form_validation_with_nonexistent_email(self):
        """Kiểm tra lỗi khi email không tồn tại"""
        form_data = {
            "email": "nonexistent@example.com",
            "password": "anypassword",
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["__all__"], [_("Email hoặc mật khẩu không chính xác.")]
        )

    def test_form_validation_with_inactive_user(self):
        """Kiểm tra lỗi khi user inactive"""
        form_data = {
            "email": "inactive@example.com",
            "password": "password123",
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["__all__"], [_("Tài khoản này đã bị vô hiệu hóa.")]
        )

    def test_form_validation_with_valid_data(self):
        """Kiểm tra form valid với email tồn tại và active"""
        form_data = {
            "email": "active@example.com",
            "password": "password123",
            "remember_me": True,
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_validation_missing_email(self):
        """Kiểm tra lỗi khi thiếu email"""
        form_data = {
            "password": "password123",
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_validation_missing_password(self):
        """Kiểm tra lỗi khi thiếu password"""
        form_data = {
            "email": "active@example.com",
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)
