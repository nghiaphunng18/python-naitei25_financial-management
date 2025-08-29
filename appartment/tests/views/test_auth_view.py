from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.contrib.messages import get_messages
from unittest.mock import patch

from ...models import Role

User = get_user_model()


class AuthViewsTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(
            role_name="Test Role", description="Role for testing"
        )

        self.user_active = User.objects.create_user(
            user_id="active_user",
            email="active@example.com",
            password="password123",
            full_name="Active User",
            phone="0123456789",
            role=self.role,
            is_active=1,
        )

        self.user_inactive = User.objects.create_user(
            user_id="inactive_user",
            email="inactive@example.com",
            password="password123",
            full_name="Inactive User",
            phone="0123456789",
            role=self.role,
            is_active=0,
        )

    def test_login_view_get_authenticated(self):
        """Test GET request khi user đã authenticated -> redirect"""
        self.client.force_login(self.user_active)
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/appartment/dashboard")

    def test_login_view_get_with_next_param(self):
        """Test GET request với next parameter -> có warning message"""
        response = self.client.get(reverse("login") + "?next=/protected/")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), _("Bạn cần đăng nhập để truy cập trang này.")
        )

    def test_login_view_get_normal(self):
        """Test GET request normal -> hiển thị form"""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/login.html")

    def test_login_view_post_inactive_user(self):
        """Test POST request với inactive user -> form error"""
        response = self.client.post(
            reverse("login"),
            {
                "email": "inactive@example.com",
                "password": "password123",
            },
        )

        self.assertEqual(response.status_code, 200)

        # Kiểm tra form có lỗi
        form = response.context["form"]
        self.assertFalse(form.is_valid())

        # Kiểm tra lỗi cụ thể
        self.assertIn("__all__", form.errors)
        self.assertIn(
            _("Tài khoản này đã bị vô hiệu hóa."), form.errors["__all__"]
        )

    @patch("django.contrib.auth.authenticate")
    def test_login_view_post_invalid_credentials(self, mock_authenticate):
        """Test POST request với invalid credentials -> error message"""
        # Mock authenticate trả về None
        mock_authenticate.return_value = None

        response = self.client.post(
            reverse("login"),
            {
                "email": "active@example.com",
                "password": "wrongpassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), _("Email hoặc mật khẩu không chính xác.")
        )

    @patch("appartment.views.auth_views.LoginForm")
    @patch("django.contrib.auth.authenticate")
    def test_login_view_post_nonexistent_email(
        self, mock_authenticate, mock_form_class
    ):
        """Test POST request với email không tồn tại -> error message"""
        # Mock form
        mock_form = mock_form_class.return_value
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = {
            "email": "nonexistent@example.com",
            "password": "password123",
        }

        # Mock authenticate trả về None
        mock_authenticate.return_value = None

        response = self.client.post(reverse("login"))

        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), _("Email hoặc mật khẩu không chính xác.")
        )

    @patch("django.contrib.auth.authenticate")
    def test_login_view_post_valid_credentials(self, mock_authenticate):
        """Test POST request với valid credentials -> login thành công"""
        # Mock authenticate trả về active user
        mock_authenticate.return_value = self.user_active

        response = self.client.post(
            reverse("login"),
            {
                "email": "active@example.com",
                "password": "password123",
            },
        )

        # Kiểm tra redirect - view redirect đến "dashboard" (name)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard"))

        # Kiểm tra message
        messages = list(get_messages(response.wsgi_request))
        welcome_messages = [
            msg for msg in messages if _("Chào mừng") in str(msg)
        ]
        self.assertEqual(len(welcome_messages), 1)

    def test_login_view_post_invalid_form(self):
        """Test POST request với form invalid -> hiển thị errors"""
        response = self.client.post(
            reverse("login"),
            {
                "email": "",  # Email trống
                "password": "password123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/login.html")

        # Kiểm tra form errors
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_logout_view_post_authenticated(self):
        """Test POST request logout khi authenticated -> logout thành công"""
        self.client.force_login(self.user_active)

        response = self.client.post(reverse("logout"))

        # Kiểm tra redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("index"))

        # Kiểm tra message
        messages = list(get_messages(response.wsgi_request))
        logout_messages = [
            msg for msg in messages if _("đăng xuất") in str(msg)
        ]
        self.assertEqual(len(logout_messages), 1)

    def test_logout_view_get_method_not_allowed(self):
        """Test GET request logout -> method not allowed"""
        self.client.force_login(self.user_active)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)
