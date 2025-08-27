from django.test import TestCase
from django.core.exceptions import ValidationError
from ...models.users import User  # Import User directly
from ...forms.profile import UserProfileForm
from ...models import Role, Province, District, Ward


class UserProfileFormTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test role
        self.role = Role.objects.create(
            role_name="role_resident", description="Test resident role"
        )

        # Create test location data
        self.province = Province.objects.create(
            province_name="Hà Nội", province_code="01"
        )
        self.district = District.objects.create(
            district_name="Ba Đình", district_code="001", province=self.province
        )
        self.ward = Ward.objects.create(
            ward_name="Phúc Xá", ward_code="00001", district=self.district
        )

        # Create test user
        self.user = User.objects.create_user(
            user_id="USER001",
            email="test@example.com",
            password="testpass123",
            full_name="Test User",
            phone="0912345678",
            role=self.role,
        )

    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {"email": "newemail@example.com", "phone": "0987654321"}
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_form_invalid_email(self):
        """Test form with invalid email"""
        form_data = {"email": "invalid-email", "phone": "0987654321"}
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_invalid_phone(self):
        """Test form with invalid phone number"""
        form_data = {
            "email": "valid@example.com",
            "phone": "123",  # Too short and invalid format
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_email_uniqueness_validation(self):
        """Test that email uniqueness is enforced"""
        # Create another user with different email
        other_user = User.objects.create_user(
            user_id="USER002",
            email="other@example.com",
            password="testpass123",
            full_name="Other User",
            phone="0912345679",
            role=self.role,
        )

        # Try to use other user's email
        form_data = {"email": "other@example.com", "phone": "0987654321"}
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn(
            "Email này đã được sử dụng bởi tài khoản khác",
            form.errors["email"][0],
        )

    def test_email_uniqueness_same_user(self):
        """Test that user can keep their own email"""
        form_data = {
            "email": "test@example.com",  # Same as current user
            "phone": "0987654321",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_phone_normalization(self):
        """Test phone number normalization"""
        form_data = {
            "email": "test@example.com",
            "phone": "+84987654321",  # Should be converted to 0987654321
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["phone"], "0987654321")

    def test_phone_with_spaces(self):
        """Test phone number with spaces and dashes"""
        form_data = {"email": "test@example.com", "phone": "098 765 4321"}
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["phone"], "0987654321")

    def test_has_changed_method_true(self):
        """Test has_changed method returns True when data changed"""
        form_data = {
            "email": "newemail@example.com",  # Different from original
            "phone": "0912345678",  # Same as original
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        form.is_valid()  # Need to validate first
        self.assertTrue(form.has_changed())

    def test_has_changed_method_false(self):
        """Test has_changed method returns False when no data changed"""
        form_data = {
            "email": "test@example.com",  # Same as original
            "phone": "0912345678",  # Same as original
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        form.is_valid()  # Need to validate first
        self.assertFalse(form.has_changed())

    def test_required_fields(self):
        """Test that email and phone are required"""
        # Empty email
        form_data = {"email": "", "phone": "0912345678"}
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

        # Empty phone
        form_data = {"email": "test@example.com", "phone": ""}
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_vietnamese_phone_patterns(self):
        """Test various Vietnamese phone number patterns"""
        valid_phones = [
            "0912345678",
            "0387654321",
            "0567891234",
            "0789123456",
            "0856789012",
            "0943216789",
            "+84912345678",
        ]

        for phone in valid_phones:
            with self.subTest(phone=phone):
                form_data = {"email": "test@example.com", "phone": phone}
                form = UserProfileForm(data=form_data, instance=self.user)
                self.assertTrue(
                    form.is_valid(), f"Phone {phone} should be valid"
                )

        invalid_phones = [
            "0212345678",  # Invalid prefix
            "091234567",  # Too short
            "09123456789",  # Too long
            "84912345678",  # Missing +
            "abcdefghij",  # Non-numeric
        ]

        for phone in invalid_phones:
            with self.subTest(phone=phone):
                form_data = {"email": "test@example.com", "phone": phone}
                form = UserProfileForm(data=form_data, instance=self.user)
                self.assertFalse(
                    form.is_valid(), f"Phone {phone} should be invalid"
                )
