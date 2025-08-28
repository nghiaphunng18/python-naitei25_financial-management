from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from ...models import MonthlyMeterReading, Room
from ...constants import StringLength, ElectricWaterStatus, RoomStatus


class MonthlyMeterReadingModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            room_id="P101", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        self.meter_reading = MonthlyMeterReading.objects.create(
            room=self.room,
            service_month=timezone.now(),
            electricity_index=100,
            water_index=50,
            status=ElectricWaterStatus.PENDING.value,
        )

    def test_monthly_meter_reading_creation(self):
        """Kiểm tra tạo MonthlyMeterReading thành công"""
        self.assertEqual(self.meter_reading.room, self.room)
        self.assertEqual(self.meter_reading.electricity_index, 100)
        self.assertEqual(self.meter_reading.water_index, 50)
        self.assertEqual(self.meter_reading.status, ElectricWaterStatus.PENDING.value)
        self.assertIsNotNone(self.meter_reading.service_month)

    def test_monthly_meter_reading_str(self):
        """Kiểm tra phương thức __str__"""
        expected_str = f"Service for Room P101 in {self.meter_reading.service_month.strftime('%Y-%m')}"
        self.assertEqual(str(self.meter_reading), expected_str)

    def test_restrict_delete_room(self):
        """Kiểm tra ràng buộc RESTRICT khi xóa Room"""
        with self.assertRaises(IntegrityError):
            self.room.delete()
