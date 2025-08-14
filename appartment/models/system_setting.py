from django.db import models
from ..constants import StringLength


# Model cho các thiết lập hệ thống
class SystemSettings(models.Model):
    setting_key = models.CharField(max_length=StringLength.LONG.value, primary_key=True)
    setting_value = models.CharField(max_length=StringLength.DESCRIPTION.value)
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.setting_key

    class Meta:
        db_table = "system_settings"  # Giữ tên bảng giống như SQL
