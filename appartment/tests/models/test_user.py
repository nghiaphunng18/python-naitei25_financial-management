from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from ...models import User, Role, Province, District, Ward
from ...constants import StringLength, UserRole


class UserModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(
            role_name=UserRole.RESIDENT.value, description="Resident role"
        )
        self.province = Province.objects.create(
            province_name="Hà Nội", province_code="HN"
        )
        self.district = District.objects.create(
            district_name="Ba Đình", district_code="BD", province=self.province
        )
        self.ward = Ward.objects.create(
            ward_name="Phúc Xá", ward_code="PX", district=self.district
        )
        self.user = User.objects.create(
            user_id="RES001",
            full_name="Nguyen Van A",
            email="a.nguyen@example.com",
            phone="0901234567",
            role=self.role,
            province=self.province,
            district=self.district,
            ward=self.ward,
            detail_address="123 Đường Láng",
            is_active=1,
        )

    def test_user_creation(self):
        self.assertEqual(self.user.user_id, "RES001")
        self.assertEqual(self.user.full_name, "Nguyen Van A")
        self.assertEqual(self.user.email, "a.nguyen@example.com")
        self.assertEqual(self.user.phone, "0901234567")
        self.assertEqual(self.user.role, self.role)
        self.assertEqual(self.user.province, self.province)
        self.assertEqual(self.user.district, self.district)
        self.assertEqual(self.user.ward, self.ward)
        self.assertEqual(self.user.detail_address, "123 Đường Láng")
        self.assertEqual(self.user.is_active, 1)
        self.assertEqual(self.user.is_deleted, 0)
        self.assertEqual(self.user.is_staff, 0)
        self.assertEqual(self.user.is_superuser, 0)
        self.assertIsNotNone(self.user.created_at)

    def test_user_str(self):
        self.assertEqual(str(self.user), "Nguyen Van A")

    def test_email_unique(self):
        """Kiểm tra ràng buộc unique của email"""
        with self.assertRaises(IntegrityError):
            User.objects.create(
                user_id="RES002",
                full_name="Nguyen Van B",
                email="a.nguyen@example.com",
                phone="0907654321",
                role=self.role,
            )

    def test_restrict_delete_role(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa Role"""
        with self.assertRaises(IntegrityError):
            self.role.delete()
