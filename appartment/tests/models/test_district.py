from django.test import TestCase
from django.db import IntegrityError
from ...models import District, Province
from ...constants import StringLength


class DistrictModelTest(TestCase):
    def setUp(self):
        self.province = Province.objects.create(
            province_name="Hà Nội", province_code="HN"
        )
        self.district = District.objects.create(
            district_name="Ba Đình", district_code="BD", province=self.province
        )

    def test_district_creation(self):
        self.assertEqual(self.district.district_name, "Ba Đình")
        self.assertEqual(self.district.district_code, "BD")
        self.assertEqual(self.district.province, self.province)

    def test_district_str(self):
        self.assertEqual(str(self.district), "Ba Đình")

    def test_restrict_delete_province(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa Province"""
        with self.assertRaises(IntegrityError):
            self.province.delete()
