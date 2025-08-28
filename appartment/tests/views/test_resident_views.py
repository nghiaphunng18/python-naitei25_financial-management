from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils import timezone

from ...models import User, Room, RoomResident, Notification, Role
from ...forms.manage.resident_room_form import ResidentRoomForm
from ...constants import UserRole, RoomStatus, NotificationStatus


class ResidentViewsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Tạo Role
        Role.objects.create(
            role_id=1, role_name=UserRole.RESIDENT.value, description="Resident role"
        )
        Role.objects.create(
            role_id=2,
            role_name=UserRole.APARTMENT_MANAGER.value,
            description="Manager role",
        )

        # Tạo User
        self.manager = User.objects.create(
            user_id="MAN001",
            full_name="Manager A",
            email="manager@example.com",
            role_id=2,
            is_active=True,
        )
        self.resident = User.objects.create(
            user_id="RES001",
            full_name="Nguyen Van A",
            email="a.nguyen@example.com",
            phone="0901234567",
            role_id=1,
            is_active=True,
        )
        self.resident2 = User.objects.create(
            user_id="RES002",
            full_name="Nguyen Van B",
            email="b.nguyen@example.com",
            phone="0907654321",
            role_id=1,
            is_active=True,
        )
        # Tạo Room
        self.room = Room.objects.create(
            room_id="P101", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        self.room_full = Room.objects.create(
            room_id="P102", status=RoomStatus.OCCUPIED.value, max_occupants=1
        )
        # Tạo RoomResident cho resident hiện tại ở room_full
        RoomResident.objects.create(
            user=self.resident,
            room=self.room_full,
            move_in_date=timezone.now() - timezone.timedelta(days=30),
            move_out_date=None,
        )
        self.client.force_login(self.manager)

    def _get_messages(self, response):
        return list(get_messages(response.wsgi_request))

    def test_resident_list_view_accessible(self):
        url = reverse("resident_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "manager/resident/resident_list.html")
        self.assertIn("form", response.context)

    def test_resident_list_filter_no_room(self):
        url = reverse("resident_list") + "?filter_status=no_room"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        residents = response.context["resident_data"]
        for resident in residents:
            self.assertEqual(resident["room_id"], "Chưa có phòng")
        self.assertTrue(
            any(resident["user_id"] == self.resident2.user_id for resident in residents)
        )

    def test_assign_room_valid(self):
        url = reverse("assign_room", kwargs={"user_id": self.resident.user_id})
        data = {"room": self.room.room_id, "csrfmiddlewaretoken": "testtoken"}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("resident_list"))
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]), "Gán phòng thành công cho cư dân Nguyen Van A."
        )
        self.assertTrue(
            RoomResident.objects.filter(user=self.resident, room=self.room).exists()
        )
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, RoomStatus.OCCUPIED.value)
        notification = Notification.objects.filter(receiver=self.resident).latest(
            "created_at"
        )
        self.assertEqual(notification.title, "Gán phòng mới")

    def test_assign_room_invalid_full_room(self):
        url = reverse("assign_room", kwargs={"user_id": self.resident2.user_id})
        data = {"room": self.room_full.room_id, "csrfmiddlewaretoken": "testtoken"}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("resident_list"))
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]), "Lỗi ở __all__: Phòng đã đầy, không thể gán thêm cư dân."
        )

    def test_assign_room_invalid_same_room(self):
        # Tạo một phòng mới với max_occupants > 1 để tránh lỗi "phòng đã đầy" từ form
        new_room = Room.objects.create(
            room_id="P103", status=RoomStatus.AVAILABLE.value, max_occupants=2
        )
        RoomResident.objects.create(
            user=self.resident,
            room=new_room,
            move_in_date=timezone.now() - timezone.timedelta(days=15),
            move_out_date=None,
        )
        url = reverse("assign_room", kwargs={"user_id": self.resident.user_id})
        data = {"room": new_room.room_id, "csrfmiddlewaretoken": "testtoken"}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("resident_list"))
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]), "Cư dân đã ở phòng P103. Vui lòng chọn phòng khác."
        )

    def test_leave_room_valid(self):
        # Kiểm tra số lượng cư dân trước khi rời
        initial_occupants = RoomResident.objects.filter(
            room=self.room_full, move_out_date__isnull=True
        ).count()
        self.assertEqual(initial_occupants, 1)
        url = reverse("leave_room", kwargs={"user_id": self.resident.user_id})
        response = self.client.post(url, {"csrfmiddlewaretoken": "testtoken"})
        self.assertRedirects(response, reverse("resident_list"))
        messages = self._get_messages(response)
        self.assertEqual(
            str(messages[0]),
            "Đã chuyển cư dân Nguyen Van A ra khỏi phòng thành công.",
        )
        room_resident = RoomResident.objects.get(
            user=self.resident, room=self.room_full
        )
        self.assertIsNotNone(room_resident.move_out_date)
        # Đảm bảo refresh trạng thái từ database
        self.room_full.refresh_from_db()
        # Kiểm tra lại số lượng cư dân sau khi rời
        remaining_occupants = RoomResident.objects.filter(
            room=self.room_full, move_out_date__isnull=True
        ).count()
        self.assertEqual(remaining_occupants, 0)
        # Thêm kiểm tra trực tiếp trạng thái từ database
        current_status = Room.objects.get(room_id=self.room_full.room_id).status
        self.assertEqual(current_status, RoomStatus.AVAILABLE.value)
        notification = Notification.objects.filter(receiver=self.resident).latest(
            "created_at"
        )
        self.assertEqual(notification.title, "Rời phòng")

    def test_leave_room_no_room(self):
        url = reverse("leave_room", kwargs={"user_id": self.resident2.user_id})
        response = self.client.post(url, {"csrfmiddlewaretoken": "testtoken"})
        self.assertRedirects(response, reverse("resident_list"))
        messages = self._get_messages(response)
        self.assertEqual(str(messages[0]), "Cư dân này hiện không ở trong phòng nào.")
