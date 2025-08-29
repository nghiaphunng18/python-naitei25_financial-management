from datetime import timedelta
import json

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from appartment.models import (
    User, Role, Province, District, Ward,
    Room, RoomResident, Bill
)
from appartment.constants import UserRole, RoomStatus, PaymentStatus


class ManagerDashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Địa chỉ (bắt buộc cho users)
        self.province = Province.objects.create(province_id=1, province_name="Hà Nội")
        self.district = District.objects.create(
            district_id=1, district_name="Đống Đa", province=self.province
        )
        self.ward = Ward.objects.create(
            ward_id=1, ward_name="Láng Hạ", district=self.district
        )

        # Role
        self.admin_role = Role.objects.create(role_id=1, role_name=UserRole.ADMIN.value)
        self.manager_role = Role.objects.create(
            role_id=2, role_name=UserRole.APARTMENT_MANAGER.value
        )
        self.resident_role = Role.objects.create(
            role_id=3, role_name=UserRole.RESIDENT.value
        )

        # User manager (đảm bảo đủ trường)
        self.manager_user = User.objects.create_user(
            email="manager@test.com",
            password="manager123",
            user_id="M1",
            full_name="Manager",
            phone="0123456789",
            role=self.manager_role,
            province=self.province,
            district=self.district,
            ward=self.ward,
        )

        # Một phòng (dùng room_id vì model mới ko có room_name)
        self.room1 = Room.objects.create(
            room_id="101",
            status=RoomStatus.OCCUPIED.value,
        )

        # Resident còn đang ở
        self.resident_user = User.objects.create_user(
            email="res@test.com",
            password="res123",
            user_id="R1",
            full_name="Resident",
            phone="0999999999",
            role=self.resident_role,
            province=self.province,
            district=self.district,
            ward=self.ward,
        )
        RoomResident.objects.create(
            room=self.room1,
            user=self.resident_user,
            move_in_date=timezone.now() - timedelta(days=30),
            move_out_date=None,
        )

        # Hóa đơn tháng này
        now = timezone.now()
        self.bill_paid = Bill.objects.create(
            bill_month=now,
            total_amount=100000,
            status=PaymentStatus.PAID.value,
            due_date=now - timedelta(days=1),
            room=self.room1,
        )
        self.bill_unpaid = Bill.objects.create(
            bill_month=now,
            total_amount=200000,
            status=PaymentStatus.UNPAID.value,
            due_date=now - timedelta(days=5),
            room=self.room1,
        )

    def login_manager(self):
        self.client.login(email="manager@test.com", password="manager123")

    def test_manager_dashboard_context(self):
        self.login_manager()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "manager/dashboard.html")

        ctx = response.context
        self.assertEqual(ctx["total_rooms"], 1)
        self.assertEqual(ctx["total_residents"], 1)
        self.assertEqual(ctx["total_occupied_rooms"], 1)
        self.assertEqual(ctx["total_bills"], 2)
        self.assertEqual(float(ctx["total_bill_money"]), 300000.0)
        self.assertEqual(ctx["total_paid_count"], 1)
        self.assertEqual(float(ctx["total_paid_money"]), 100000.0)
        self.assertIn(self.bill_unpaid, list(ctx["overdue_bills"]))

        months_labels = json.loads(ctx["months_labels"])
        months_amounts = json.loads(ctx["months_amounts"])
        self.assertEqual(len(months_labels), 6)
        self.assertEqual(len(months_amounts), 6)

    def test_dashboard_for_roles(self):
        # Admin
        admin_user = User.objects.create_user(
            email="admin@test.com",
            password="admin123",
            user_id="A1",
            full_name="Admin",
            phone="0111111111",
            role=self.admin_role,
            province=self.province,
            district=self.district,
            ward=self.ward,
        )
        self.client.login(email="admin@test.com", password="admin123")
        response = self.client.get(reverse("dashboard"))
        self.assertTemplateUsed(response, "admin/dashboard.html")

        # Resident
        self.client.login(email="res@test.com", password="res123")
        response = self.client.get(reverse("dashboard"))
        self.assertTemplateUsed(response, "resident/dashboard.html")
