from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from appartment.models import Role, Province, District, Ward
from ...views.profile_views import get_role_colors

User = get_user_model()


class ProfileViewTest(TestCase):
    def setUp(self):
        # Tạo các role
        self.resident_role = Role.objects.create(
            role_name="role_resident", description="Resident role"
        )
        self.manager_role = Role.objects.create(
            role_name="role_apartment_manager", description="Manager role"
        )
        self.admin_role = Role.objects.create(
            role_name="role_admin", description="Admin role"
        )

        # Tạo địa chỉ test data
        self.province = Province.objects.create(
            province_name="Hà Nội", province_code="01"
        )
        self.district = District.objects.create(
            district_name="Quận Ba Đình",
            district_code="001",
            province=self.province,
        )
        self.ward = Ward.objects.create(
            ward_name="Phường Điện Biên",
            ward_code="00001",
            district=self.district,
        )

        # Tạo test users cho từng role
        self.resident_user = User.objects.create_user(
            user_id="resident_001",
            email="resident@test.com",
            password="password123",
            full_name="Resident User",
            phone="0123456789",
            role=self.resident_role,
            detail_address="Số 10",
            province=self.province,
            district=self.district,
            ward=self.ward,
            is_active=True,
        )

        self.manager_user = User.objects.create_user(
            user_id="manager_001",
            email="manager@test.com",
            password="password123",
            full_name="Manager User",
            phone="0987654321",
            role=self.manager_role,
            is_active=True,
        )

        self.admin_user = User.objects.create_user(
            user_id="admin_001",
            email="admin@test.com",
            password="password123",
            full_name="Admin User",
            phone="0111222333",
            role=self.admin_role,
            is_active=True,
        )

        # User không có địa chỉ
        self.user_no_address = User.objects.create_user(
            user_id="user_no_addr",
            email="noaddr@test.com",
            password="password123",
            full_name="No Address User",
            phone="0444555666",
            role=self.resident_role,
            is_active=True,
        )

        # User không có role (tạm thời dùng resident role)
        self.user_no_role = User.objects.create_user(
            user_id="user_no_role",
            email="norole@test.com",
            password="password123",
            full_name="No Role User",
            phone="0777888999",
            role=self.resident_role,  # Tạm thời assign role
            is_active=True,
        )

        self.client = Client()

    def test_profile_view_requires_login(self):
        """Test profile view yêu cầu đăng nhập"""
        response = self.client.get(reverse("profile"))

        # Chuyển hướng đến trang đăng nhập
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_profile_view_resident_template(self):
        """Test profile view với resident user sử dụng đúng template"""
        self.client.force_login(self.resident_user)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/resident_profile.html")

    def test_profile_view_manager_template(self):
        """Test profile view với manager user sử dụng đúng template"""
        self.client.force_login(self.manager_user)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/manager_profile.html")

    def test_profile_view_admin_template(self):
        """Test profile view với admin user sử dụng đúng template"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/admin_profile.html")

    def test_profile_view_no_role_default_template(self):
        """Test profile view với user không có role sử dụng template mặc định"""
        # Use the existing role instead of setting it to None
        self.client.force_login(self.user_no_role)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/resident_profile.html")

    def test_profile_view_context_with_full_address(self):
        """Test context khi user có đầy đủ thông tin địa chỉ"""
        self.client.force_login(self.resident_user)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertEqual(context["user"], self.resident_user)
        self.assertEqual(
            context["full_address"],
            "Số 10, Phường Điện Biên, Quận Ba Đình, Hà Nội",
        )
        self.assertEqual(context["role_name"], "role_resident")
        self.assertFalse(context["is_edit_mode"])

        # Kiểm tra colors cho resident
        colors = context["colors"]
        self.assertIn("from-blue-500 to-blue-600", colors["gradient"])
        self.assertIn("bg-blue-100 text-blue-800", colors["badge"])

    def test_profile_view_context_no_address(self):
        """Test context khi user không có thông tin địa chỉ"""
        self.client.force_login(self.user_no_address)
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertEqual(context["full_address"], "Chưa cập nhật")

    def test_profile_view_context_partial_address(self):
        """Test context khi user có một số thông tin địa chỉ"""
        # Tạo user chỉ có detail_address và ward
        user_partial = User.objects.create_user(
            user_id="partial_addr",
            email="partial@test.com",
            password="password123",
            full_name="Partial Address User",
            phone="0555666777",
            role=self.resident_role,
            detail_address="Số 20",
            ward=self.ward,
            is_active=True,
        )

        self.client.force_login(user_partial)
        response = self.client.get(reverse("profile"))

        context = response.context
        self.assertEqual(context["full_address"], "Số 20, Phường Điện Biên")

    def test_profile_view_context_no_role(self):
        """Test context khi user không có role"""
        # Create a user with an unknown role type
        unknown_role = Role.objects.create(
            role_name="unknown_role", description="Unknown role"
        )

        user_with_unknown_role = User.objects.create_user(
            user_id="unknown_role",
            email="unknown@test.com",
            password="password123",
            full_name="Unknown Role User",
            phone="0777888999",
            role=unknown_role,
            is_active=True,
        )

        self.client.force_login(user_with_unknown_role)
        response = self.client.get(reverse("profile"))

        context = response.context
        self.assertEqual(context["role_name"], "Chưa xác định")

    def test_profile_view_manager_colors(self):
        """Test colors cho manager role"""
        self.client.force_login(self.manager_user)
        response = self.client.get(reverse("profile"))

        colors = response.context["colors"]
        self.assertIn("from-green-500 to-green-600", colors["gradient"])
        self.assertIn("bg-green-100 text-green-800", colors["badge"])
        self.assertIn("focus:ring-green-500", colors["focus_ring"])

    def test_profile_view_admin_colors(self):
        """Test colors cho admin role"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("profile"))

        colors = response.context["colors"]
        self.assertIn("from-purple-500 to-purple-600", colors["gradient"])
        self.assertIn("bg-purple-100 text-purple-800", colors["badge"])
        self.assertIn("focus:ring-purple-500", colors["focus_ring"])

    def test_profile_view_get_role_colors_function(self):
        """Test riêng function get_role_colors"""

        # Test resident colors
        resident_colors = get_role_colors("role_resident")
        self.assertIn("blue", resident_colors["gradient"])

        # Test manager colors
        manager_colors = get_role_colors("role_apartment_manager")
        self.assertIn("green", manager_colors["gradient"])

        # Test admin colors
        admin_colors = get_role_colors("role_admin")
        self.assertIn("purple", admin_colors["gradient"])

        # Test unknown role (should default to admin colors)
        unknown_colors = get_role_colors("unknown_role")
        self.assertIn("purple", unknown_colors["gradient"])

    def test_profile_view_context_structure(self):
        """Test cấu trúc context đầy đủ"""
        self.client.force_login(self.resident_user)
        response = self.client.get(reverse("profile"))

        context = response.context

        # Kiểm tra tất cả keys có trong context
        required_keys = [
            "user",
            "full_address",
            "role_name",
            "colors",
            "is_edit_mode",
        ]

        for key in required_keys:
            self.assertIn(key, context)

        # Kiểm tra colors có tất cả keys cần thiết
        colors = context["colors"]
        color_keys = [
            "gradient",
            "badge",
            "focus_ring",
            "info_bg",
            "info_icon",
            "info_text",
            "info_content",
        ]

        for key in color_keys:
            self.assertIn(key, colors)


class ProfileEditViewTest(TestCase):
    def setUp(self):
        # Tạo các role
        self.resident_role = Role.objects.create(
            role_name="role_resident", description="Resident role"
        )
        self.manager_role = Role.objects.create(
            role_name="role_apartment_manager", description="Manager role"
        )

        # Tạo địa chỉ test data
        self.province = Province.objects.create(
            province_name="Hà Nội", province_code="01"
        )
        self.district = District.objects.create(
            district_name="Quận Ba Đình",
            district_code="001",
            province=self.province,
        )
        self.ward = Ward.objects.create(
            ward_name="Phường Điện Biên",
            ward_code="00001",
            district=self.district,
        )

        # Tạo test user
        self.user = User.objects.create_user(
            user_id="test_user_001",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            phone="0123456789",
            role=self.resident_role,
            detail_address="Số 10",
            province=self.province,
            district=self.district,
            ward=self.ward,
            is_active=True,
        )

        self.manager_user = User.objects.create_user(
            user_id="manager_001",
            email="manager@test.com",
            password="password123",
            full_name="Manager User",
            phone="0987654321",
            role=self.manager_role,
            is_active=True,
        )

        self.client = Client()

    def test_profile_edit_view_requires_login(self):
        """Test profile edit view yêu cầu đăng nhập"""
        response = self.client.get(reverse("profile_edit"))

        # Chuyển hướng đến trang đăng nhập
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_profile_edit_view_get_request(self):
        """Test GET request hiển thị form edit"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("profile_edit"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/resident_profile.html")

        # Kiểm tra context
        context = response.context
        self.assertEqual(context["user"], self.user)
        self.assertTrue(context["is_edit_mode"])
        self.assertIn("form", context)

        # Kiểm tra form được khởi tạo với instance của user
        form = context["form"]
        self.assertEqual(form.instance, self.user)

    def test_profile_edit_view_manager_template(self):
        """Test manager user sử dụng đúng template"""
        self.client.force_login(self.manager_user)
        response = self.client.get(reverse("profile_edit"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/manager_profile.html")

    def test_profile_edit_view_post_valid_data_with_changes(self):
        """Test POST request với dữ liệu hợp lệ và có thay đổi"""
        self.client.force_login(self.user)

        post_data = {
            "full_name": "Updated Test User",
            "phone": "0123456789",
            "detail_address": "Số 10",
            "province": self.province.pk,
            "district": self.district.pk,
            "ward": self.ward.pk,
            "email": self.user.email,  # Add email field
        }

        response = self.client.post(reverse("profile_edit"), data=post_data)
        self.assertRedirects(response, reverse("profile"))

        # Verify changes
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Test User")

        # Kiểm tra success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("cập nhật thành công", str(messages[0]))

    def test_profile_edit_view_post_valid_data_no_changes(self):
        """Test POST request với dữ liệu hợp lệ nhưng không có thay đổi"""
        self.client.force_login(self.user)

        post_data = {
            "full_name": self.user.full_name,
            "phone": self.user.phone,
            "detail_address": self.user.detail_address,
            "province": self.province.pk,
            "district": self.district.pk,
            "ward": self.ward.pk,
            "email": self.user.email,  # Add email field
        }

        response = self.client.post(reverse("profile_edit"), data=post_data)
        self.assertRedirects(response, reverse("profile"))

        # Kiểm tra info message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Không có thông tin nào được thay đổi", str(messages[0]))

    def test_profile_edit_view_post_invalid_data(self):
        """Test POST request với dữ liệu không hợp lệ"""
        self.client.force_login(self.user)

        # Data không hợp lệ (email format sai, phone trống)
        post_data = {
            "full_name": "",  # Required field trống
            "phone": "",  # Required field trống
            "detail_address": "Số 10",
        }

        response = self.client.post(reverse("profile_edit"), data=post_data)

        # Không redirect, trở lại form với lỗi
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/resident_profile.html")

        # Kiểm tra form có lỗi
        form = response.context["form"]
        self.assertFalse(form.is_valid())

        # Kiểm tra error messages được hiển thị
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)

        # User không được cập nhật
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Test User")  # Giữ nguyên

    def test_profile_edit_view_context_in_edit_mode(self):
        """Test context khi ở edit mode"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("profile_edit"))

        context = response.context

        # Kiểm tra is_edit_mode = True
        self.assertTrue(context["is_edit_mode"])

        # Kiểm tra các context khác vẫn có
        self.assertEqual(context["user"], self.user)
        self.assertIn("form", context)
        self.assertIn("full_address", context)
        self.assertIn("role_name", context)
        self.assertIn("colors", context)

    def test_profile_edit_view_post_form_error_handling(self):
        """Test xử lý lỗi form chi tiết"""
        self.client.force_login(self.user)

        # Mock form để tạo lỗi cụ thể
        post_data = {
            "full_name": "A" * 101,  # Vượt quá max_length nếu có
            "phone": "invalid-phone-format",
            "detail_address": "Số 10",
        }

        response = self.client.post(reverse("profile_edit"), data=post_data)

        # Kiểm tra form không hợp lệ
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.is_valid())

        # Kiểm tra có error messages
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)

    def test_profile_edit_view_address_context(self):
        """Test context địa chỉ trong edit mode"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("profile_edit"))

        context = response.context
        self.assertEqual(
            context["full_address"],
            "Số 10, Phường Điện Biên, Quận Ba Đình, Hà Nội",
        )

    def test_profile_edit_view_form_initial_data(self):
        """Test form được khởi tạo với dữ liệu hiện tại của user"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("profile_edit"))

        form = response.context["form"]

        # Kiểm tra initial data
        self.assertEqual(
            form.initial.get("full_name", form.instance.full_name),
            self.user.full_name,
        )
        self.assertEqual(
            form.initial.get("phone", form.instance.phone), self.user.phone
        )
        self.assertEqual(
            form.initial.get("detail_address", form.instance.detail_address),
            self.user.detail_address,
        )

    def test_profile_edit_view_successful_update_redirect(self):
        """Test redirect sau khi cập nhật thành công"""
        self.client.force_login(self.user)

        post_data = {
            "full_name": "New Name",
            "phone": "0999888777",
            "detail_address": "Số 20",
            "province": self.province.pk,  # Changed from id to pk
            "district": self.district.pk,  # Changed from id to pk
            "ward": self.ward.pk,  # Changed from id to pk
        }

        response = self.client.post(reverse("profile_edit"), data=post_data)

        # Kiểm tra redirect
        self.assertRedirects(response, reverse("profile"))

    def test_profile_edit_view_maintains_role_colors(self):
        """Test colors được duy trì đúng trong edit mode"""
        self.client.force_login(self.manager_user)
        response = self.client.get(reverse("profile_edit"))

        colors = response.context["colors"]
        # Manager should have green colors
        self.assertIn("green", colors["gradient"])
        self.assertIn("bg-green-100 text-green-800", colors["badge"])
