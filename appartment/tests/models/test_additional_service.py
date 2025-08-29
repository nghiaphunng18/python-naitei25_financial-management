from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from ...models import AdditionalService
from ...constants import StringLength, ServiceType, DecimalConfig


class AdditionalServiceModelTest(TestCase):
    def setUp(self):
        self.service = AdditionalService.objects.create(
            name="Wi-Fi",
            type=ServiceType.PER_ROOM.value,
            description="Internet tốc độ cao",
            unit_price=100000.00,
        )

    def test_additional_service_creation(self):
        self.assertEqual(self.service.name, "Wi-Fi")
        self.assertEqual(self.service.type, ServiceType.PER_ROOM.value)
        self.assertEqual(self.service.description, "Internet tốc độ cao")
        self.assertEqual(self.service.unit_price, 100000.00)
        self.assertIsNotNone(self.service.created_at)

    def test_additional_service_str(self):
        self.assertEqual(str(self.service), "Wi-Fi")

    def test_name_max_length(self):
        """Kiểm tra giới hạn độ dài của name"""
        max_length = StringLength.EXTRA_LONG.value
        long_name = "A" * (max_length + 1)
        with self.assertRaises(Exception):
            AdditionalService.objects.create(
                name=long_name, type=ServiceType.PER_ROOM.value, unit_price=100000.00
            )

    def test_type_choices(self):
        """Kiểm tra giá trị type nằm trong choices"""
        service = AdditionalService(
            name="Invalid Service",
            type="INVALID_TYPE",  # Giá trị không hợp lệ
            unit_price=100000.00,
        )
        with self.assertRaises(ValidationError):
            service.full_clean()
