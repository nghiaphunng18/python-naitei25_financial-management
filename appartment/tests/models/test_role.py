from django.test import TestCase
from ...models import Role
from ...constants import StringLength, UserRole


class RoleModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(
            role_name=UserRole.RESIDENT.value, description="Resident role"
        )

    def test_role_creation(self):
        self.assertEqual(self.role.role_name, UserRole.RESIDENT.value)
        self.assertEqual(self.role.description, "Resident role")

    def test_role_str(self):
        self.assertEqual(str(self.role), UserRole.RESIDENT.value)
