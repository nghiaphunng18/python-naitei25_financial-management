# appartment/tests/test_views_manager.py

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date
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
    SystemSettings,
    Notification,
)
from ...constants import UserRole


class ManagerBillingViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        setUpTestData chạy một lần duy nhất cho cả class test.
        """
        # 1. Tạo các đối tượng cơ bản
        cls.role_manager = Role.objects.create(
            role_id=2, role_name=UserRole.APARTMENT_MANAGER.value
        )
        cls.role_resident = Role.objects.create(
            role_id=3, role_name=UserRole.RESIDENT.value
        )

        cls.manager = User.objects.create_user(
            email="manager@example.com",
            password="password123",
            user_id="manager01",
            role=cls.role_manager,
            is_staff=True,
        )

        cls.resident1 = User.objects.create_user(
            email="resident1@example.com",
            password="pw",
            user_id="res01",
            role=cls.role_resident,
        )
        cls.resident2 = User.objects.create_user(
            email="resident2@example.com",
            password="pw",
            user_id="res02",
            role=cls.role_resident,
        )

        cls.room101 = Room.objects.create(
            room_id="P101", description="Phòng 101", area=25, status="occupied"
        )
        cls.room102 = Room.objects.create(
            room_id="P102", description="Phòng 102", area=35, status="available"
        )

        RoomResident.objects.create(
            room=cls.room101, user=cls.resident1, move_in_date=date(2025, 1, 1)
        )
        RoomResident.objects.create(
            room=cls.room101, user=cls.resident2, move_in_date=date(2025, 2, 1)
        )

        cls.service_internet = AdditionalService.objects.create(
            name="Internet", unit_price=250000, type="PER_ROOM"
        )
        cls.service_parking = AdditionalService.objects.create(
            name="Gửi xe", unit_price=100000, type="PER_PERSON"
        )

        RentalPrice.objects.create(
            room=cls.room101, price=5000000, effective_date=date(2025, 1, 1)
        )

        # SỬA LẠI: Thêm SystemSettings vào dữ liệu test
        SystemSettings.objects.create(
            setting_key="ELECTRICITY_UNIT_PRICE", setting_value="3500"
        )
        SystemSettings.objects.create(
            setting_key="WATER_UNIT_PRICE", setting_value="10000"
        )

        cls.test_month = date(2025, 8, 1)
        cls.prev_month = date(2025, 7, 1)

    def setUp(self):
        self.client = Client()
        self.client.login(email="manager@example.com", password="password123")

    # --- TESTS FOR BILLING WORKSPACE ---

    def test_billing_workspace_loads_successfully(self):
        url = reverse("billing_workspace")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "manager/bills/billing_workspace.html")

    # --- TESTS FOR SAVEMETERREADINGVIEW ---

    def test_save_meter_reading_success(self):
        ElectricWaterTotal.objects.create(
            summary_for_month=self.test_month,
            total_electricity=500,
            total_water=50,
            electricity_cost=1750000,
            water_cost=500000,
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

    def test_save_meter_reading_fail_exceed_total(self):
        ElectricWaterTotal.objects.create(
            summary_for_month=self.test_month,
            total_electricity=100,
            total_water=10,
            electricity_cost=350000,
            water_cost=100000,
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
        response = self.client.post(url, post_data, follow=True)
        messages = list(response.context.get("messages", []))
        self.assertEqual(len(messages), 1)
        self.assertIn("vượt quá tổng của tòa nhà", str(messages[0]))
        self.assertFalse(
            MonthlyMeterReading.objects.filter(
                room=self.room101, service_month=self.test_month
            ).exists()
        )

    # --- TESTS FOR ADDADHOCSERVICEVIEW ---

    def test_add_adhoc_service_success_json_response(self):
        url = reverse("add_adhoc_service")
        post_data = {
            "room": self.room101.pk,
            "service": self.service_internet.pk,
            "bill_month": self.test_month.strftime("%Y-%m"),
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertTrue(
            DraftBill.objects.filter(
                room=self.room101, bill_month=self.test_month, draft_type="SERVICES"
            ).exists()
        )

    def test_add_per_room_service_twice_fails_json_response(self):
        """Kiểm tra việc thêm dịch vụ theo phòng 2 lần sẽ thất bại."""
        # Thêm lần đầu tiên
        self.client.post(
            reverse("add_adhoc_service"),
            {
                "room": self.room101.pk,
                "service": self.service_internet.pk,
                "bill_month": self.test_month.strftime("%Y-%m"),
            },
        )

        # Thử thêm lần thứ hai
        url = reverse("add_adhoc_service")
        post_data = {
            "room": self.room101.pk,
            "service": self.service_internet.pk,
            "bill_month": self.test_month.strftime("%Y-%m"),
        }
        response = self.client.post(url, post_data)

        # SỬA LẠI: Kiểm tra JSON response, không phải context
        self.assertEqual(
            response.status_code, 400
        )  # Lỗi do người dùng -> 400 Bad Request
        response_data = response.json()
        self.assertEqual(response_data["status"], "error")
        self.assertIn("chỉ có thể thêm một lần", response_data["message"])

    def test_add_per_person_service_exceeds_limit_fails_json_response(self):
        """Kiểm tra thêm dịch vụ theo người thất bại khi quá số lượng."""
        # Phòng 101 có 2 người, thêm 2 lần gửi xe
        self.client.post(
            reverse("add_adhoc_service"),
            {
                "room": self.room101.pk,
                "service": self.service_parking.pk,
                "bill_month": self.test_month.strftime("%Y-%m"),
            },
        )
        self.client.post(
            reverse("add_adhoc_service"),
            {
                "room": self.room101.pk,
                "service": self.service_parking.pk,
                "bill_month": self.test_month.strftime("%Y-%m"),
            },
        )

        # Thử thêm lần thứ 3
        url = reverse("add_adhoc_service")
        post_data = {
            "room": self.room101.pk,
            "service": self.service_parking.pk,
            "bill_month": self.test_month.strftime("%Y-%m"),
        }
        response = self.client.post(url, post_data)

        # SỬA LẠI: Kiểm tra JSON response và status code 400
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("Đã đạt số lượng tối đa", response.json()["message"])

    # --- TESTS FOR GENERATEFINALBILLVIEW ---

    def test_generate_final_bill_success(self):
        """Kiểm tra tổng hợp hóa đơn cuối cùng thành công."""
        DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            draft_type="ELECTRIC_WATER",
            status="CONFIRMED",
            total_amount=500000,
            details={},
        )
        DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            draft_type="SERVICES",
            status="CONFIRMED",
            total_amount=250000,
            details={"services": []},
        )

        url = reverse("generate_final_bill")
        post_data = {
            "room_id": self.room101.pk,
            "month": self.test_month.strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Bill.objects.filter(
                room=self.room101, bill_month__month=self.test_month.month
            ).exists()
        )

    def test_generate_final_bill_fails_if_not_confirmed(self):
        """Kiểm tra tạo HĐ cuối cùng thất bại nếu HĐ nháp chưa được xác nhận."""
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
        response = self.client.post(url, post_data, follow=True)
        messages = list(response.context.get("messages", []))

        self.assertEqual(len(messages), 1)
        self.assertIn("chưa có đủ 2 HĐ nháp được xác nhận", str(messages[0]))
        self.assertFalse(
            Bill.objects.filter(
                room=self.room101, bill_month__month=self.test_month.month
            ).exists()
        )

    def test_building_utility_total_view_get(self):
        """Kiểm tra trang nhập tổng điện nước tải thành công."""
        url = reverse("utility_totals")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_building_utility_total_view_post_success(self):
        """Kiểm tra việc POST dữ liệu tổng điện nước thành công."""
        url = reverse("utility_totals")
        post_data = {
            "summary_for_month": "2025-09-01",
            "total_electricity": "1000",
            "total_water": "100",
            "electricity_cost": "3500000",
            "water_cost": "1000000",
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(
            ElectricWaterTotal.objects.filter(
                summary_for_month=date(2025, 9, 1)
            ).exists()
        )

    def test_building_utility_total_view_post_invalid_data(self):
        """Kiểm tra POST dữ liệu không hợp lệ vào trang nhập tổng."""
        url = reverse("utility_totals")
        post_data = {"summary_for_month": "invalid-date"}  # Thiếu các trường khác
        response = self.client.post(url, post_data, follow=True)
        messages = list(response.context.get("messages", []))
        self.assertIn("Vui lòng điền đầy đủ", str(messages[0]))

    def test_draft_bill_detail_view_loads(self):
        """Kiểm tra trang chi tiết hóa đơn nháp tải thành công."""
        draft_bill = DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            draft_type="SERVICES",
            total_amount=1000,
            status="SENT",
        )
        url = reverse("draft_bill_detail", kwargs={"pk": draft_bill.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["draft_bill"], draft_bill)

    def test_update_draft_bill_status_success(self):
        """Kiểm tra việc cập nhật trạng thái HĐ nháp thành công."""
        # SỬA LẠI: Thêm total_amount khi tạo
        draft_bill = DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            status="SENT",
            total_amount=1000,
        )
        url = reverse("update_draft_bill_status", kwargs={"pk": draft_bill.pk})
        post_data = {"status": "CONFIRMED"}

        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)  # Sau redirect là 200

        draft_bill.refresh_from_db()
        self.assertEqual(draft_bill.status, "CONFIRMED")

    def test_update_draft_bill_status_invalid_status(self):
        """Kiểm tra việc cập nhật HĐ nháp với trạng thái không hợp lệ."""
        # SỬA LẠI: Thêm total_amount khi tạo
        draft_bill = DraftBill.objects.create(
            room=self.room101,
            bill_month=self.test_month,
            status="SENT",
            total_amount=1000,
        )
        url = reverse("update_draft_bill_status", kwargs={"pk": draft_bill.pk})
        post_data = {"status": "INVALID_STATUS"}
        response = self.client.post(url, post_data, follow=True)
        messages = list(response.context.get("messages", []))
        self.assertIn("Trạng thái không hợp lệ", str(messages[0]))

    def test_add_adhoc_service_form_invalid(self):
        """Kiểm tra AddAdhocServiceView khi form không hợp lệ."""
        url = reverse("add_adhoc_service")
        post_data = {"room": self.room101.pk}  # Thiếu service và bill_month
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 400)  # Lỗi Bad Request
        self.assertEqual(response.json()["status"], "error")

    def test_send_payment_reminders_success(self):
        """Kiểm tra chức năng gửi nhắc nhở thanh toán."""
        # Tạo một hóa đơn quá hạn
        overdue_bill = Bill.objects.create(
            room=self.room101,
            bill_month=self.prev_month,
            status="unpaid",
            due_date=date(2025, 7, 15),
            total_amount=1000,
        )

        url = reverse("send_payment_reminders")
        post_data = {
            "bill_ids": [overdue_bill.pk],
            "month_param": self.test_month.strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, post_data, follow=True)
        messages = list(response.context.get("messages", []))

        self.assertIn("Đã gửi thành công", str(messages[0]))
        # Kiểm tra xem notification đã được tạo cho cư dân trong phòng chưa
        self.assertTrue(Notification.objects.filter(receiver=self.resident1).exists())

    def test_send_payment_reminders_no_bills_selected(self):
        """Kiểm tra gửi nhắc nhở khi không chọn hóa đơn nào."""
        url = reverse("send_payment_reminders")
        post_data = {"bill_ids": []}  # Không có ID nào
        response = self.client.post(url, post_data, follow=True)
        messages = list(response.context.get("messages", []))
        self.assertIn("Vui lòng chọn ít nhất một hóa đơn", str(messages[0]))
