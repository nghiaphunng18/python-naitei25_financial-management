from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import datetime

from appartment.models import (
    Role,
    Province,
    District,
    Ward,
    User,
    Room,
    DraftBill,
    SystemSettings,
    AdditionalService,
    MonthlyMeterReading,
)


class ManagerBillingViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # --- Tạo role ---
        self.role_manager = Role.objects.create(role_name="Manager")

        # --- Tạo Province / District / Ward ---
        self.province = Province.objects.create(
            province_name="Test Province", province_code="TP01"
        )
        self.district = District.objects.create(
            district_name="Test District", district_code="TD01", province=self.province
        )
        self.ward = Ward.objects.create(
            ward_name="Test Ward", ward_code="TW01", district=self.district
        )

        # --- Tạo user manager ---
        self.manager = User.objects.create(
            user_id="M001",
            full_name="Manager Test",
            email="manager@test.com",
            phone="0123456789",
            role=self.role_manager,
            province=self.province,
            district=self.district,
            ward=self.ward,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        self.client.force_login(self.manager)

        # --- Tạo phòng ---
        self.room101 = Room.objects.create(room_id="P101", area=30.0)

        # --- Tháng test ---
        self.test_month = timezone.make_aware(datetime(2025, 8, 1))
        self.prev_month = timezone.make_aware(datetime(2025, 7, 1))

        # --- SystemSettings ---
        SystemSettings.objects.create(
            setting_key="ELECTRICITY_UNIT_PRICE", setting_value="3000"
        )
        SystemSettings.objects.create(
            setting_key="WATER_UNIT_PRICE", setting_value="2000"
        )

        # --- Additional service ---
        self.service1 = AdditionalService.objects.create(
            name="Dịch vụ test", type="per_room", unit_price=100000
        )

        # --- DraftBill ---
        self.ew_draft = DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            draft_type="ELECTRIC_WATER",
            status="CONFIRMED",
            total_amount=500000,
            details={"electric_cost": 300000, "water_cost": 200000},  # dict, không None
        )

    def test_save_meter_reading_success(self):
        url = reverse("save_meter_reading", args=[self.room101.room_id])
        post_data = {
            "room_id": self.room101.room_id,
            "electricity_index": 100,
            "water_index": 50,
            "service_month": self.test_month.strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertTrue(any("success" in str(m).lower() for m in messages))

    def test_save_meter_reading_fail_exceed_total(self):
        url = reverse("save_meter_reading", args=[self.room101.room_id])
        post_data = {
            "room_id": self.room101.room_id,
            "electricity_index": 999999,
            "water_index": 999999,
            "service_month": self.test_month.strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, post_data, follow=True)
        messages = list(response.context["messages"])
        self.assertTrue(any("exceed" in str(m).lower() for m in messages))

    def test_generate_final_bill_success(self):
        url = reverse("generate_final_bill")
        post_data = {
            "room_id": self.room101.room_id,
            "bill_month": self.test_month.strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_generate_services_bill_success(self):
        url = reverse("generate_services_bill")  # không truyền args
        post_data = {
            "room_id": self.room101.room_id,
            "bill_month": self.test_month.strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_add_adhoc_service_success(self):
        url = reverse("add_adhoc_service")
        post_data = {
            "room_id": self.room101.room_id,
            "service_id": self.service1.service_id,
            "service_month": self.test_month.strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, post_data)
        # giả sử view redirect sau khi add
        self.assertEqual(response.status_code, 302)

    def test_draft_bill_details_not_none(self):
        self.assertIsNotNone(self.ew_draft.details)
        self.assertIsInstance(self.ew_draft.details, dict)
