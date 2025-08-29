# appartment/tests/views/test_room_history_views.py
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages

from appartment.constants import UserRole, PRICE_CHANGES_PER_PAGE_MAX
from appartment.models import Room, RentalPrice, RoomResident, User
from appartment.models.districts import District
from appartment.models.provinces import Province
from appartment.models.roles import Role
from appartment.models.wards import Ward


class GetRoomHistoryViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # ---- Tạo dữ liệu liên quan tối thiểu để thỏa ràng buộc FK ----
        self.province = Province.objects.create(
            province_id=1, province_name="Ha Noi", province_code="HN"
        )
        self.district = District.objects.create(
            district_id=1, province=self.province, district_name="Quan Dong Da"
        )
        self.ward = Ward.objects.create(
            ward_id=1, district=self.district, ward_name="Phuong Lang Thuong"
        )

        # ---- Role cho Manager ----
        # Dùng đúng chuỗi mà view kiểm tra (thường là "ROLE_APARTMENT_MANAGER")
        self.role_manager = Role.objects.create(
            role_id=1, role_name="ROLE_APARTMENT_MANAGER"
        )

        # ---- User có role Manager và đăng nhập ----
        self.user = User.objects.create_user(
            full_name="manager",
            password="test123",
            email="manager@example.com",
            phone="0123456789",
            province=self.province,
            district=self.district,
            ward=self.ward,
            role=self.role_manager,
            is_active=True,
        )
        self.client.force_login(self.user)

        # ---- Phòng để test ----
        self.room = Room.objects.create(
            room_id="T101",
            area=20,
            description="Phòng test",
            status="OCCUPIED",
            max_occupants=3,
            created_at=timezone.now(),
        )

    def _messages(self, response):
        return [m.message for m in get_messages(response.wsgi_request)]

    def test_room_not_exist_redirects(self):
        response = self.client.get(reverse("room_history", args=[999]), follow=True)
        final_path = response.request.get("PATH_INFO", "")
        self.assertEqual(final_path, reverse("room_list"))
        msgs = self._messages(response)
        self.assertTrue(any("Phòng có ID 999 không tồn tại." in m for m in msgs))

    def test_room_history_without_prices_or_residents(self):
        response = self.client.get(reverse("room_history", args=[self.room.room_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "room_history.html")
        context = response.context
        self.assertIn("history_page_obj", context)
        history_page = context["history_page_obj"]
        self.assertGreaterEqual(len(history_page.object_list), 1)

    def test_room_history_with_prices(self):
        RentalPrice.objects.create(
            room=self.room,
            price=Decimal("1000000"),
            effective_date=timezone.now() - timedelta(days=200),
        )
        RentalPrice.objects.create(
            room=self.room,
            price=Decimal("2000000"),
            effective_date=timezone.now() - timedelta(days=50),
        )

        response = self.client.get(reverse("room_history", args=[self.room.room_id]))
        self.assertEqual(response.status_code, 200)

        history_page = response.context["history_page_obj"].object_list
        prices_in_history = [h.get("price") for h in history_page]
        self.assertIn(
            Decimal("2000000"), [p for p in prices_in_history if p is not None]
        )

    def test_room_history_with_residents(self):
    # Role resident cũng phải đúng format
        role_resident = Role.objects.create(role_id=2, role_name="ROLE_RESIDENT")

        # Tạo user bằng .create(...) và set_password + save() để tránh lỗi created_at NULL
        user1 = User.objects.create(
            user_id="res1",  # PK phải là giá trị riêng biệt
            full_name="resident1",
            email="resident1@gmail.com",
            phone="0123456789",
            province=self.province,
            district=self.district,
            ward=self.ward,
            role=role_resident,
            is_active=True,
            date_joined=timezone.now(),
            created_at=timezone.now(),   # bắt buộc để tránh NULL
        )
        user1.set_password("test123")
        user1.save()

        user2 = User.objects.create(
            user_id="res2",
            full_name="resident2",
            email="resident2@gmail.com",
            phone="0123456789",
            province=self.province,
            district=self.district,
            ward=self.ward,
            role=role_resident,
            is_active=True,
            date_joined=timezone.now(),
            created_at=timezone.now(),
        )
        user2.set_password("test123")
        user2.save()

        # Tạo RoomResident (timezone-aware)
        RoomResident.objects.create(
            room=self.room,
            user=user1,
            move_in_date=timezone.now() - timedelta(days=100),
            move_out_date=None,
        )
        RoomResident.objects.create(
            room=self.room,
            user=user2,
            move_in_date=timezone.now() - timedelta(days=300),
            move_out_date=timezone.now() - timedelta(days=150),
        )

        # Login lại bằng manager để đảm bảo quyền
        self.client.force_login(self.user)

        response = self.client.get(reverse("room_history", args=[self.room.room_id]))
        # giờ phải trả về 200
        self.assertEqual(response.status_code, 200)

        history = response.context["history_page_obj"].object_list
        resident_counts = [h["number_of_residents"] for h in history]
        self.assertTrue(any(c > 0 for c in resident_counts))

    def test_pagination_price_changes(self):
        total = PRICE_CHANGES_PER_PAGE_MAX + 5
        for i in range(total):
            RentalPrice.objects.create(
                room=self.room,
                price=Decimal("1000000") + i,
                effective_date=timezone.now() - timedelta(days=i),
            )

        url = reverse("room_history", args=[self.room.room_id]) + "?page1=2"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("price_page_obj", response.context)
        price_page = response.context["price_page_obj"]
        self.assertTrue(price_page.has_previous())
