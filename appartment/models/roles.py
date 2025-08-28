from django.db import models

from ..constants import StringLength


class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=StringLength.MEDIUM.value)
    description = models.CharField(
        max_length=StringLength.EXTRA_LONG.value, null=True, blank=True
    )

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.role_name
