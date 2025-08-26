from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date
from ...constants import UserRole
import json

# Import các model bạn cần để tạo dữ liệu
from ...models import (
    User,
    Room,
    Role,
    DraftBill,
    ElectricWaterTotal,
    MonthlyMeterReading,
    AdditionalService,
    RoomResident,
    Bill,
    RentalPrice,
)


class ManagerBillingViewsTest(TestCase):

    def setUp(self):
        """
        Phương thức này được chạy TRƯỚC MỖI test case.
        Nó tạo ra một database sạch và các đối tượng cần thiết.
        """
        # 1. Tạo Role cho manager và resident
        self.role_manager = Role.objects.create(
            role_id=1, name=UserRole.APARTMENT_MANAGER.value
        )
        self.role_resident = Role.objects.create(role_id=2, name="RESIDENT")

        # 2. Tạo manager user
        self.manager = User.objects.create_user(
            email="manager@example.com",
            password="password123",
            user_id="manager01",
            full_name="Manager User",
            role=self.role_manager,
            is_staff=True,  # cần thiết cho StaffRequiredMixin
        )

        # 3. Tạo các phòng
        self.room101 = Room.objects.create(
            room_id="P101", description="Phòng 101", area=25
        )
        self.room102 = Room.objects.create(
            room_id="P102", description="Phòng 102", area=35
        )

        # 4. Dữ liệu cho các dịch vụ
        self.service_internet = AdditionalService.objects.create(
            name="Internet", unit_price=250000, type="PER_ROOM"
        )
        self.service_parking = AdditionalService.objects.create(
            name="Gửi xe", unit_price=100000, type="PER_PERSON"
        )

        # 5. Tạo client và đăng nhập
        self.client = Client()
        self.client.login(email="manager@example.com", password="password123")

        # 6. Chuẩn bị các biến ngày tháng
        self.test_month = date(2025, 8, 1)
        self.prev_month = date(2025, 7, 1)

    def test_save_meter_reading_success(self):
        """Kiểm tra trường hợp lưu chỉ số thành công."""
        ElectricWaterTotal.objects.create(
            summary_for_month=self.test_month,
            total_electricity=500,
            total_water=50,
        )
        MonthlyMeterReading.objects.create(
            room=self.room101,
            service_month=self.prev_month,
            electricity_index=1000,
            water_index=50,
        )

        url = reverse("save_meter_reading", kwargs={"room_id": self.room101.pk})
        post_data = {
            "month": self.test_month.strftime("%Y-%m-%d"),
            "electricity_index": "1150",
            "water_index": "60",
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            MonthlyMeterReading.objects.filter(
                room=self.room101, service_month=self.test_month
            ).exists()
        )
        self.assertTrue(
            DraftBill.objects.filter(
                room=self.room101,
                bill_month=self.test_month,
                draft_type="ELECTRIC_WATER",
            ).exists()
        )

    def test_save_meter_reading_fail_exceed_total(self):
        """Kiểm tra trường hợp lưu chỉ số thất bại do vượt quá tổng tòa nhà."""
        ElectricWaterTotal.objects.create(
            summary_for_month=self.test_month,
            total_electricity=100,
            total_water=10,
        )
        MonthlyMeterReading.objects.create(
            room=self.room101, service_month=self.prev_month, electricity_index=1000
        )

        url = reverse("save_meter_reading", kwargs={"room_id": self.room101.pk})
        post_data = {
            "month": self.test_month.strftime("%Y-%m-%d"),
            "electricity_index": "1150",
            "water_index": "60",
        }
        response = self.client.post(url, post_data)
        messages = list(response.context["messages"])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(messages), 1)
        self.assertIn("vượt quá tổng của tòa nhà", str(messages[0]))
        self.assertFalse(
            MonthlyMeterReading.objects.filter(
                room=self.room101, service_month=self.test_month
            ).exists()
        )

    def test_generate_services_bill_success(self):
        """Kiểm tra chức năng tạo hóa đơn dịch vụ hàng loạt."""
        resident_user = User.objects.create_user(
            email="resident@example.com",
            password="pw",
            user_id="res01",
            full_name="Resident User",
            role=self.role_resident,
        )
        RoomResident.objects.create(
            room=self.room102, user=resident_user, move_in_date=self.prev_month
        )

        url = reverse("generate_services_bill_for_month")
        post_data = {"month": self.test_month.strftime("%Y-%m-%d")}
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            DraftBill.objects.filter(
                room=self.room102, bill_month=self.test_month, draft_type="SERVICES"
            ).exists()
        )
        self.assertFalse(
            DraftBill.objects.filter(
                room=self.room101, bill_month=self.test_month, draft_type="SERVICES"
            ).exists()
        )

    def test_billing_workspace_view_loads(self):
        url = reverse("billing_workspace")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "manager/bills/billing_workspace.html")

    def test_billing_workspace_filters_by_occupied_rooms(self):
        url = (
            reverse("billing_workspace")
            + f'?month={self.test_month.strftime("%Y-%m-%d")}'
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["workspace_data"]), 1)
        self.assertEqual(response.context["workspace_data"][0]["room"], self.room101)

    def test_add_adhoc_service_success(self):
        url = reverse("add_adhoc_service")
        post_data = {
            "room": self.room101.pk,
            "service": self.service_internet.pk,
            "bill_month": "2025-08",
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        draft_bill = DraftBill.objects.get(
            room=self.room101, bill_month=self.test_month, draft_type="SERVICES"
        )
        self.assertEqual(draft_bill.total_amount, self.service_internet.unit_price)
        self.assertEqual(len(draft_bill.details["services"]), 1)

    def test_add_per_room_service_twice_fails(self):
        DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            draft_type="SERVICES",
            total_amount=self.service_internet.unit_price,
            details={
                "services": [
                    {
                        "service_id": self.service_internet.pk,
                        "cost": float(self.service_internet.unit_price),
                    }
                ]
            },
        )
        url = reverse("add_adhoc_service")
        post_data = {
            "room": self.room101.pk,
            "service": self.service_internet.pk,
            "bill_month": "2025-08",
        }
        response = self.client.post(url, post_data)
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("chỉ có thể thêm một lần", str(messages[0]))

    def test_generate_final_bill_success(self):
        DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            draft_type="ELECTRIC_WATER",
            status="CONFIRMED",
            total_amount=500000,
        )
        DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            draft_type="SERVICES",
            status="CONFIRMED",
            total_amount=250000,
        )
        RentalPrice.objects.create(
            room=self.room101, price=5000000, effective_date=date(2025, 1, 1)
        )

        url = reverse("generate_final_bill")
        post_data = {
            "room_id": self.room101.pk,
            "month": self.test_month.strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        final_bill = Bill.objects.get(
            room=self.room101, bill_month__month=self.test_month.month
        )
        self.assertEqual(final_bill.total_amount, 5000000 + 500000 + 250000)
        self.assertEqual(final_bill.status, "unpaid")

    def test_generate_final_bill_fails_if_not_confirmed(self):
        DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            draft_type="ELECTRIC_WATER",
            status="SENT",
            total_amount=500000,
        )
        DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            draft_type="SERVICES",
            status="SENT",
            total_amount=250000,
        )

        url = reverse("generate_final_bill")
        post_data = {
            "room_id": self.room101.pk,
            "month": self.test_month.strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, post_data)
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("chưa có đủ 2 HĐ nháp được xác nhận", str(messages[0]))
        self.assertFalse(
            Bill.objects.filter(
                room=self.room101, bill_month__month=self.test_month.month
            ).exists()
        )
