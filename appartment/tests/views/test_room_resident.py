from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now
from django.utils import timezone
import warnings
from datetime import timedelta

from appartment.models import (
    Room,
    RoomResident,
    User,
    RentalPrice,
    Province,
    District,
    Ward,
    Role,
)
from appartment.constants import UserRole


class ResidentRoomViewsTest(TestCase):
    def setUp(self):
        warnings.filterwarnings(
            "ignore",
            category=RuntimeWarning,
            message="DateTimeField .* received a naive datetime.*",
        )
        self.client = Client()

        # tạo dữ liệu liên quan
        self.province = Province.objects.create(
            province_id=1, province_name="Ha Noi", province_code="HN"
        )
        self.district = District.objects.create(
            district_id=1, province=self.province, district_name="Quan Dong Da"
        )
        self.ward = Ward.objects.create(
            ward_id=1, district=self.district, ward_name="Phuong Lang Thuong"
        )
        self.role = Role.objects.create(role_id=1, role_name="ROLE_RESIDENT")

        # tạo user
        self.user = User.objects.create_user(
            full_name="resident",
            password="test123",
            email="resident@gmail.com",
            phone="0123456789",
            province=self.province,
            district=self.district,
            ward=self.ward,
            role=self.role,
            is_active=True,
        )

        self.client.force_login(self.user)

        self.room = Room.objects.create(
            room_id="T101",
            area=20,
            description="Phòng test",
            status="OCCUPIED",
            max_occupants=3,
        )

    def test_room_list_success(self):
        # gán resident vào room
        RoomResident.objects.create(
            room=self.room,
            user=self.user,
            move_in_date=timezone.now() - timezone.timedelta(days=30),
            move_out_date=None,
        )

        url = reverse("resident_room_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("room_infos", response.context)
        self.assertEqual(response.context["room_infos"][0]["status"], "Đang ở")

    def test_room_list_no_rooms(self):
        url = reverse("resident_room_list")
        response = self.client.get(url)
        # redirect về dashboard vì ko có room_resident
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("dashboard"), response.url)

    def test_room_detail_success(self):
        rr = RoomResident.objects.create(
            room=self.room,
            user=self.user,
            move_in_date=timezone.now() - timezone.timedelta(days=30),
            move_out_date=None,
        )

        url = reverse("resident_room_detail", args=[rr.room.room_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["status"], "Đang ở")
        self.assertEqual(response.context["room_id"], rr.room.room_id)

    def test_room_detail_not_exist(self):
        url = reverse("resident_room_detail", args=[self.room.room_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("resident_room_list"), response.url)

    def test_room_history_success(self):
        rr = RoomResident.objects.create(
            room=self.room,
            user=self.user,
            move_in_date=timezone.now() - timezone.timedelta(days=30),
            move_out_date=None,
        )

        # Thêm giá thuê để test
        RentalPrice.objects.create(
            room=rr.room,
            price=1000,
            effective_date=timezone.now() - timezone.timedelta(days=15),
        )

        url = reverse("resident_room_history", args=[rr.room.room_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("price_page_obj", response.context)
        self.assertIn("history_page_obj", response.context)

    def test_room_history_not_exist(self):
        url = reverse("resident_room_history", args=[self.room.room_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("resident_room_list"), response.url)
