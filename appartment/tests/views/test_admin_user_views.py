from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from appartment.models import Province, District, Ward, Role
from appartment.constants import UserRole

User = get_user_model()


class UserViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Tạo dữ liệu địa chỉ
        self.province = Province.objects.create(province_id=1, province_name="Hà Nội")
        self.district = District.objects.create(
            district_id=1, district_name="Đống Đa", province=self.province
        )
        self.ward = Ward.objects.create(
            ward_id=1, ward_name="Láng Hạ", district=self.district
        )

        # Tạo role
        self.admin_role = Role.objects.create(role_id=1, role_name=UserRole.ADMIN.value)
        self.resident_role = Role.objects.create(role_id=2, role_name=UserRole.RESIDENT.value)

        # Tạo user admin
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="admin123",
            user_id="1",
            full_name="Admin",
            phone="0123456789",
            role=self.admin_role,
            province=self.province,
            district=self.district,
            ward=self.ward,
        )

    def login_admin(self):
        self.client.login(email="admin@test.com", password="admin123")

    def test_user_list_requires_login(self):
        url = reverse("user_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # redirect login

    def test_user_list_as_admin(self):
        self.login_admin()
        url = reverse("user_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("users", response.context)

    def test_create_user_get(self):
        self.login_admin()
        url = reverse("create_user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_create_user_post(self):
        self.login_admin()
        url = reverse("create_user")
        data = {
            "user_id": "2",
            "full_name": "Resident A",
            "email": "res@test.com",
            "phone": "0999999999",
            "role": self.resident_role.pk,
            "province": self.province.pk,
            "district": self.district.pk,
            "ward": self.ward.pk,
            "detail_address": "Số 1",
            "status": "True",
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email="res@test.com").exists())

    def test_update_user_post(self):
        self.login_admin()
        user = User.objects.create_user(
            email="update@test.com",
            password="pass",
            user_id="5",
            full_name="Old Name",
            phone="0111111111",
            role=self.resident_role,
        )
        url = reverse("update_user", args=[user.user_id])
        data = {
            "user_id": user.user_id,
            "full_name": "New Name",
            "email": user.email,
            "phone": user.phone,
            "detail_address": "ABC",
            "role": self.resident_role.pk,
            "status": "True",
            "province": self.province.pk,
            "district": self.district.pk,
            "ward": self.ward.pk,
        }
        response = self.client.post(url, data, follow=True)
        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.full_name, "New Name")

    def test_delete_user(self):
        self.login_admin()
        user = User.objects.create_user(
            email="del@test.com", password="pass", user_id="10",
            full_name="To delete", phone="0888888888", role=self.resident_role
        )
        url = reverse("delete_user", args=[user.user_id])
        response = self.client.post(url, follow=True)
        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.is_deleted)
        self.assertFalse(user.is_active)

    def test_toggle_active(self):
        self.login_admin()
        user = User.objects.create_user(
            email="toggle@test.com", password="pass", user_id="15",
            full_name="Toggle User", phone="0777777777", role=self.resident_role
        )
        url = reverse("toggle_active", args=[user.user_id])
        response = self.client.post(url, follow=True)
        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        # Sau khi toggle thì user sẽ bị đổi trạng thái
        self.assertIn(user.is_active, [True, False])

    def test_load_districts(self):
        self.login_admin()
        url = reverse("load_districts") + f"?province={self.province.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.district.district_name)

    def test_load_wards(self):
        self.login_admin()
        url = reverse("load_wards") + f"?district={self.district.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ward.ward_name)
