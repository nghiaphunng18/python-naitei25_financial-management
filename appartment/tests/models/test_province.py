from django.test import TestCase
from ...models import Province
from ...constants import StringLength


class ProvinceModelTest(TestCase):
    def setUp(self):
        self.province = Province.objects.create(
            province_name="Hà Nội", province_code="HN"
        )

    def test_province_creation(self):
        self.assertEqual(self.province.province_name, "Hà Nội")
        self.assertEqual(self.province.province_code, "HN")

    def test_province_str(self):
        self.assertEqual(str(self.province), "Hà Nội")
