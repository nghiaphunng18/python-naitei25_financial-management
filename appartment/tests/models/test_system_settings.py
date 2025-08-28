from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from ...models import SystemSettings
from ...constants import StringLength


class SystemSettingsModelTest(TestCase):
    def setUp(self):
        self.setting = SystemSettings.objects.create(
            setting_key="MAX_LOGIN_ATTEMPTS",
            setting_value="5",
            description="Số lần đăng nhập tối đa",
        )

    def test_system_settings_creation(self):
        self.assertEqual(self.setting.setting_key, "MAX_LOGIN_ATTEMPTS")
        self.assertEqual(self.setting.setting_value, "5")
        self.assertEqual(self.setting.description, "Số lần đăng nhập tối đa")
        self.assertIsNotNone(self.setting.updated_at)

    def test_system_settings_str(self):
        self.assertEqual(str(self.setting), "MAX_LOGIN_ATTEMPTS")

    def test_setting_key_unique(self):
        with self.assertRaises(IntegrityError):
            SystemSettings.objects.create(
                setting_key="MAX_LOGIN_ATTEMPTS", setting_value="10"
            )
