# appartment/tests/views/test_rental_price.py
from decimal import Decimal
import warnings
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils import timezone

from appartment.models import (
    Room,
    RentalPrice,
    User,
    Province,
    District,
    Ward,
    Role,
)
from appartment.constants import UserRole


class RentalPriceViewsTest(TestCase):
    def setUp(self):
        warnings.filterwarnings(
            "ignore",
            category=RuntimeWarning,
            message="DateTimeField .* received a naive datetime.*",
        )
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
        self.role_manager = Role.objects.create(
            role_id=1, role_name=UserRole.APARTMENT_MANAGER.value
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
        )

    # Helper lấy toàn bộ messages của response cuối cùng (sau khi follow redirect)
    def _messages(self, response):
        return [m.message for m in get_messages(response.wsgi_request)]

    # ------------------ CREATE ------------------
    def test_rental_price_create_success(self):
        url = reverse("rental_price_create", args=[self.room.room_id])
        data = {
            "price": "2000000",
            "effective_date": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        response = self.client.post(url, data, follow=True)

        # Redirect về room_detail
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(
                reverse("room_detail", args=[self.room.room_id]) in u
                for u, _ in response.redirect_chain
            )
        )

        # Đã tạo bản ghi
        self.assertTrue(
            RentalPrice.objects.filter(
                room=self.room, price=Decimal("2000000")
            ).exists()
        )

        # Có message thành công
        msgs = self._messages(response)
        self.assertTrue(any("Thêm giá mới" in m for m in msgs))

    def test_rental_price_create_room_not_exist(self):
        url = reverse("rental_price_create", args=[9999])  # room_id không tồn tại
        response = self.client.post(
            url,
            {
                "price": "2000000",
                "effective_date": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
        # View redirect về room_detail
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("room_detail", args=[9999]), response.url)

        def test_rental_price_create_invalid_form(self):
            # Gửi dữ liệu không hợp lệ: price không phải số, effective_date sai định dạng
            url = reverse("rental_price_create", args=[self.room.room_id])
            data = {"price": "abc", "effective_date": "invalid-datetime"}
            response = self.client.post(url, data, follow=True)

            # View của bạn redirect về room_detail mà KHÔNG thêm message lỗi (đúng logic hiện tại)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                any(
                    reverse("room_detail", args=[self.room.room_id]) in u
                    for u, _ in response.redirect_chain
                )
            )
            self.assertEqual(RentalPrice.objects.filter(room=self.room).count(), 0)

    # ------------------ UPDATE ------------------
    def test_rental_price_update_success(self):
        # Tạo giá thuê ban đầu
        rp = RentalPrice.objects.create(
            room=self.room,
            price=Decimal("1000000"),
            effective_date=timezone.now() - timezone.timedelta(days=10),
        )

        url = reverse("rental_price_update", args=[rp.rental_price_id])

        # Data update: dùng YYYY-MM-DD cho DateField
        data = {
            "price": "3000000",
            "effective_date": (timezone.now() + timezone.timedelta(days=1))
            .date()
            .strftime("%Y-%m-%d"),
        }

        response = self.client.post(url, data)
        rp.refresh_from_db()

        self.assertEqual(response.status_code, 302)  # Redirect về room_detail
        self.assertEqual(rp.price, Decimal("3000000"))  # Giá đã update

    def test_rental_price_update_not_exist(self):
        url = reverse("rental_price_update", args=[999999])
        data = {
            "price": "1234",
            "effective_date": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        response = self.client.post(url, data, follow=True)

        # Redirect về room_list
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(reverse("room_list") in u for u, _ in response.redirect_chain)
        )

        # Message lỗi
        msgs = self._messages(response)
        self.assertTrue(any("không tồn tại" in m for m in msgs))

    def test_rental_price_update_invalid_form(self):
        rp = RentalPrice.objects.create(
            room=self.room,
            price=Decimal("1000"),
            effective_date=timezone.now(),
        )
        url = reverse("rental_price_update", args=[rp.rental_price_id])
        data = {"price": "abc", "effective_date": "invalid"}
        response = self.client.post(url, data, follow=True)

        # Không đổi dữ liệu
        rp.refresh_from_db()
        self.assertEqual(rp.price, Decimal("1000"))

        # Redirect về room_detail + có message lỗi
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(
                reverse("room_detail", args=[self.room.room_id]) in u
                for u, _ in response.redirect_chain
            )
        )
        msgs = self._messages(response)
        self.assertTrue(any("Dữ liệu không hợp lệ" in m for m in msgs))

    # ------------------ DELETE ------------------
    def test_rental_price_delete_success(self):
        rp = RentalPrice.objects.create(
            room=self.room,
            price=Decimal("5000"),
            effective_date=timezone.now(),
        )
        url = reverse("rental_price_delete", args=[rp.rental_price_id])
        response = self.client.post(url, follow=True)

        # Đã xóa
        self.assertFalse(RentalPrice.objects.filter(pk=rp.pk).exists())

        # Redirect về room_detail + message thành công
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(
                reverse("room_detail", args=[self.room.room_id]) in u
                for u, _ in response.redirect_chain
            )
        )
        msgs = self._messages(response)
        self.assertTrue(any("Đã xóa giá thuê phòng thành công" in m for m in msgs))

    def test_rental_price_delete_not_exist(self):
        url = reverse("rental_price_delete", args=[999999])
        response = self.client.post(url, follow=True)

        # Redirect về room_list + message lỗi
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(reverse("room_list") in u for u, _ in response.redirect_chain)
        )
        msgs = self._messages(response)
        self.assertTrue(any("không tồn tại" in m for m in msgs))

    def test_rental_price_delete_invalid_method_get(self):
        rp = RentalPrice.objects.create(
            room=self.room,
            price=Decimal("7000"),
            effective_date=timezone.now(),
        )
        url = reverse("rental_price_delete", args=[rp.rental_price_id])
        response = self.client.get(url, follow=True)

        # Không xóa, redirect về room_detail + message lỗi
        self.assertTrue(RentalPrice.objects.filter(pk=rp.pk).exists())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(
                reverse("room_detail", args=[self.room.room_id]) in u
                for u, _ in response.redirect_chain
            )
        )
        msgs = self._messages(response)
        self.assertTrue(any("Yêu cầu không hợp lệ" in m for m in msgs))
