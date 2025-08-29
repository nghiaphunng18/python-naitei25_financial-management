from django.test import TestCase
from django import forms
from unittest.mock import patch
from ....forms.manager.room_forms import CreateRoomForm, UpdateRoomForm
from ....models import Room
from ....constants import RoomStatus, MIN_OCCUPANTS, MAX_OCCUPANTS


class CreateRoomFormTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Tạo một room đã tồn tại để test uniqueness
        self.existing_room = Room.objects.create(
            room_id="A101",
            area=25.5,
            description="Test room",
            status=RoomStatus.AVAILABLE.value,
            max_occupants=4,
        )

    def test_form_fields_present(self):
        """Test that form has correct fields"""
        form = CreateRoomForm()
        expected_fields = [
            "room_id",
            "area",
            "description",
            "status",
            "max_occupants",
        ]
        self.assertEqual(list(form.fields.keys()), expected_fields)

    def test_form_field_widgets_and_attributes(self):
        """Test form field widgets and attributes"""
        form = CreateRoomForm()

        # Test room_id field
        self.assertIn("class", form.fields["room_id"].widget.attrs)
        self.assertIn("placeholder", form.fields["room_id"].widget.attrs)

        # Test area field
        self.assertIn("step", form.fields["area"].widget.attrs)
        self.assertEqual(form.fields["area"].widget.attrs["step"], "0.01")

        # Test description field
        self.assertIn("rows", form.fields["description"].widget.attrs)
        self.assertEqual(form.fields["description"].widget.attrs["rows"], 4)

        # Test max_occupants field
        self.assertIn("min", form.fields["max_occupants"].widget.attrs)
        self.assertEqual(
            form.fields["max_occupants"].widget.attrs["min"], str(MIN_OCCUPANTS)
        )

    def test_form_field_labels(self):
        """Test Vietnamese field labels"""
        form = CreateRoomForm()

        self.assertEqual(str(form.fields["room_id"].label), "Tên phòng")
        self.assertEqual(str(form.fields["area"].label), "Diện tích (m²)")
        self.assertEqual(str(form.fields["description"].label), "Mô tả")
        self.assertEqual(str(form.fields["status"].label), "Trạng thái")
        self.assertEqual(
            str(form.fields["max_occupants"].label), "Số người tối đa"
        )

    def test_required_fields(self):
        """Test required fields"""
        form = CreateRoomForm()
        self.assertTrue(form.fields["room_id"].required)
        self.assertTrue(form.fields["max_occupants"].required)
        self.assertFalse(form.fields["area"].required)
        self.assertFalse(form.fields["description"].required)

    def test_valid_form_data(self):
        """Test form with valid data"""
        form_data = {
            "room_id": "B202",
            "area": 30.0,
            "description": "Nice room",
            "status": RoomStatus.AVAILABLE.value,
            "max_occupants": 6,
        }
        form = CreateRoomForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_room_id_required(self):
        """Test that room_id is required"""
        form_data = {"area": 30.0, "max_occupants": 6}
        form = CreateRoomForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("room_id", form.errors)

    def test_max_occupants_required(self):
        """Test that max_occupants is required"""
        form_data = {
            "room_id": "B202",
            "area": 30.0,
        }
        form = CreateRoomForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("max_occupants", form.errors)

    def test_room_id_uniqueness_validation(self):
        """Test room_id uniqueness validation"""
        form_data = {
            "room_id": "A101",  # Already exists
            "area": 30.0,
            "max_occupants": 6,
        }
        form = CreateRoomForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("room_id", form.errors)
        self.assertIn(
            "Tên phòng này đã tồn tại. Vui lòng chọn tên khác.",
            form.errors["room_id"],
        )

    def test_area_validation_positive(self):
        """Test area must be positive"""
        # Test zero area
        form_data = {"room_id": "B202", "area": 0, "max_occupants": 6}
        form = CreateRoomForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("area", form.errors)
        self.assertIn("Diện tích phải lớn hơn 0.", form.errors["area"])

        # Test negative area
        form_data["area"] = -5.0
        form = CreateRoomForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("area", form.errors)

    def test_area_validation_none(self):
        """Test area can be None (optional field)"""
        form_data = {
            "room_id": "B202",
            "area": None,
            "status": RoomStatus.AVAILABLE.value,
            "max_occupants": 6,
        }
        form = CreateRoomForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors.as_data())

    def test_max_occupants_validation_range(self):
        """Test max_occupants validation within range"""
        # Test below minimum
        form_data = {
            "room_id": "B202",
            "area": 30.0,
            "status": RoomStatus.AVAILABLE.value,
            "max_occupants": 0,  # Below MIN_OCCUPANTS (1)
        }
        form = CreateRoomForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("max_occupants", form.errors)
        self.assertIn(
            f"Số người tối thiểu phải ít nhất là {MIN_OCCUPANTS}.",
            form.errors["max_occupants"],
        )

        # Test above maximum
        form_data["max_occupants"] = 11  # Above MAX_OCCUPANTS (10)
        form = CreateRoomForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("max_occupants", form.errors)
        self.assertIn(
            f"Số người tối đa không được vượt quá {MAX_OCCUPANTS}.",
            form.errors["max_occupants"],
        )

    def test_form_save(self):
        """Test form save functionality"""
        form_data = {
            "room_id": "C303",
            "area": 35.0,
            "description": "Large room",
            "status": RoomStatus.AVAILABLE.value,
            "max_occupants": 8,
        }
        form = CreateRoomForm(data=form_data)
        self.assertTrue(form.is_valid())

        room = form.save()
        self.assertEqual(room.room_id, "C303")
        self.assertEqual(room.area, 35.0)
        self.assertEqual(room.description, "Large room")
        self.assertEqual(room.max_occupants, 8)


class UpdateRoomFormTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.room = Room.objects.create(
            room_id="A101",
            area=25.5,
            description="Test room",
            status=RoomStatus.AVAILABLE.value,
            max_occupants=4,
        )

    def test_form_fields_present(self):
        """Test that form has correct fields (no room_id)"""
        form = UpdateRoomForm()
        expected_fields = ["area", "description", "status", "max_occupants"]
        self.assertEqual(list(form.fields.keys()), expected_fields)

    def test_form_initialization_with_current_occupants(self):
        """Test form initialization with current occupants"""
        form = UpdateRoomForm(current_occupants=3)
        self.assertEqual(form.current_occupants, 3)

        # Check help text is added
        help_text = form.fields["max_occupants"].help_text
        self.assertIn("Hiện có 3 người đang ở", str(help_text))

    def test_form_initialization_without_current_occupants(self):
        """Test form initialization without current occupants"""
        form = UpdateRoomForm()
        self.assertEqual(form.current_occupants, 0)

        # No help text should be added
        help_text = form.fields["max_occupants"].help_text
        self.assertEqual(help_text, "")

    def test_valid_form_data(self):
        """Test form with valid data"""
        form_data = {
            "area": 30.0,
            "description": "Updated room",
            "status": RoomStatus.AVAILABLE.value,
            "max_occupants": 6,
        }
        form = UpdateRoomForm(data=form_data, instance=self.room)
        self.assertTrue(form.is_valid())

    def test_area_validation_positive(self):
        """Test area must be positive"""
        form_data = {
            "area": -5.0,
            "status": RoomStatus.AVAILABLE.value,
            "max_occupants": 4,
        }
        form = UpdateRoomForm(data=form_data, instance=self.room)
        self.assertFalse(form.is_valid())
        self.assertIn("area", form.errors)
        self.assertIn("Diện tích phải lớn hơn 0.", form.errors["area"])

    def test_max_occupants_validation_basic_range(self):
        """Test max_occupants validation for basic range"""
        # Test below minimum
        form_data = {
            "area": 30.0,
            "status": RoomStatus.AVAILABLE.value,
            "max_occupants": 0,  # Below MIN_OCCUPANTS (1)
        }
        form = UpdateRoomForm(data=form_data, instance=self.room)
        self.assertFalse(form.is_valid())
        self.assertIn("max_occupants", form.errors)
        self.assertIn(
            f"Số người tối thiểu phải ít nhất là {MIN_OCCUPANTS}.",
            form.errors["max_occupants"],
        )

        # Test above maximum
        form_data["max_occupants"] = 11  # Above MAX_OCCUPANTS (10)
        form = UpdateRoomForm(data=form_data, instance=self.room)
        self.assertFalse(form.is_valid())
        self.assertIn("max_occupants", form.errors)
        self.assertIn(
            f"Số người tối đa không được vượt quá {MAX_OCCUPANTS}.",
            form.errors["max_occupants"],
        )

    def test_max_occupants_validation_with_current_occupants(self):
        """Test max_occupants cannot be less than current occupants"""
        form_data = {
            "area": 30.0,
            "status": RoomStatus.AVAILABLE.value,
            "max_occupants": 2,  # Less than current occupants (3)
        }
        form = UpdateRoomForm(
            data=form_data, instance=self.room, current_occupants=3
        )
        self.assertFalse(form.is_valid())
        self.assertIn("max_occupants", form.errors)

        error_msg = form.errors["max_occupants"][0]
        self.assertIn(
            "không thể nhỏ hơn số người đang ở hiện tại", str(error_msg)
        )
        self.assertIn("2", str(error_msg))  # max_occupants value
        self.assertIn("3", str(error_msg))  # current_occupants value

    def test_max_occupants_validation_equal_current_occupants(self):
        """Test max_occupants can equal current occupants"""
        form_data = {
            "area": 30.0,
            "status": RoomStatus.AVAILABLE.value,
            "max_occupants": 3,  # Equal to current occupants
        }
        form = UpdateRoomForm(
            data=form_data, instance=self.room, current_occupants=3
        )
        self.assertTrue(form.is_valid())

    def test_status_validation_unavailable_with_occupants(self):
        """Test cannot set status to unavailable when there are occupants"""
        form_data = {
            "area": 30.0,
            "status": RoomStatus.UNAVAILABLE.value,
            "max_occupants": 4,
        }
        form = UpdateRoomForm(
            data=form_data, instance=self.room, current_occupants=2
        )
        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)
        self.assertIn(
            "Không thể chuyển sang trạng thái Unavailable khi vẫn còn người ở.",
            form.errors["status"],
        )

    def test_status_validation_unavailable_without_occupants(self):
        """Test can set status to unavailable when no occupants"""
        form_data = {
            "area": 30.0,
            "status": RoomStatus.UNAVAILABLE.value,
            "max_occupants": 4,
        }
        form = UpdateRoomForm(
            data=form_data, instance=self.room, current_occupants=0
        )
        self.assertTrue(form.is_valid())

    def test_status_validation_maintenance_with_occupants(self):
        """Test can set status to maintenance even with occupants"""
        form_data = {
            "area": 30.0,
            "status": RoomStatus.MAINTENANCE.value,
            "max_occupants": 4,
        }
        form = UpdateRoomForm(
            data=form_data, instance=self.room, current_occupants=2
        )
        self.assertTrue(form.is_valid())

    def test_form_save_with_current_occupants(self):
        """Test form save functionality with current occupants tracking"""
        form_data = {
            "area": 35.0,
            "description": "Updated room description",
            "status": RoomStatus.OCCUPIED.value,
            "max_occupants": 6,
        }
        form = UpdateRoomForm(
            data=form_data, instance=self.room, current_occupants=3
        )
        self.assertTrue(form.is_valid())

        updated_room = form.save()
        self.assertEqual(updated_room.area, 35.0)
        self.assertEqual(updated_room.description, "Updated room description")
        self.assertEqual(updated_room.status, RoomStatus.OCCUPIED.value)
        self.assertEqual(updated_room.max_occupants, 6)

    def test_field_labels(self):
        """Test Vietnamese field labels"""
        form = UpdateRoomForm()

        self.assertEqual(str(form.fields["area"].label), "Diện tích (m²)")
        self.assertEqual(str(form.fields["description"].label), "Mô tả")
        self.assertEqual(str(form.fields["status"].label), "Trạng thái")
        self.assertEqual(
            str(form.fields["max_occupants"].label), "Số người tối đa"
        )

    def test_required_fields(self):
        """Test required fields"""
        form = UpdateRoomForm()
        self.assertTrue(form.fields["max_occupants"].required)
        self.assertFalse(form.fields["area"].required)
        self.assertFalse(form.fields["description"].required)

    def test_complex_validation_scenario(self):
        """Test complex scenario with multiple validations"""
        # Try to update room with invalid data
        form_data = {
            "area": -10.0,  # Invalid: negative area
            "status": RoomStatus.UNAVAILABLE.value,  # Invalid: unavailable with occupants
            "max_occupants": 2,  # Invalid: less than current occupants (3)
        }
        form = UpdateRoomForm(
            data=form_data, instance=self.room, current_occupants=3
        )
        self.assertFalse(form.is_valid())

        # Should have multiple errors
        self.assertIn("area", form.errors)
        self.assertIn("status", form.errors)
        self.assertIn("max_occupants", form.errors)

    def test_edge_case_zero_current_occupants(self):
        """Test edge case with zero current occupants"""
        form_data = {
            "area": 30.0,
            "status": RoomStatus.UNAVAILABLE.value,
            "max_occupants": 1,  # Valid as it meets MIN_OCCUPANTS
        }
        form = UpdateRoomForm(
            data=form_data, instance=self.room, current_occupants=0
        )
        self.assertTrue(form.is_valid())
