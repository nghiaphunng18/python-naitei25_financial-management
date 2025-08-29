from django.test import TestCase
from django.db import IntegrityError
from ...models import Ward, District, Province
from ...constants import StringLength


class WardModelTest(TestCase):
    def setUp(self):
        self.province = Province.objects.create(
            province_name="Hà Nội", province_code="HN"
        )
        self.district = District.objects.create(
            district_name="Ba Đình", district_code="BD", province=self.province
        )
        self.ward = Ward.objects.create(
            ward_name="Phúc Xá", ward_code="PX", district=self.district
        )

    def test_ward_creation(self):
        self.assertEqual(self.ward.ward_name, "Phúc Xá")
        self.assertEqual(self.ward.ward_code, "PX")
        self.assertEqual(self.ward.district, self.district)

    def test_ward_str(self):
        self.assertEqual(str(self.ward), "Phúc Xá")

    def test_restrict_delete_district(self):
        with self.assertRaises(IntegrityError):
            self.district.delete()
