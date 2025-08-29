from django.db import models

from ..constants import StringLength


class Province(models.Model):
    province_id = models.AutoField(primary_key=True)
    province_name = models.CharField(max_length=StringLength.MEDIUM.value)
    province_code = models.CharField(max_length=StringLength.MEDIUM.value)

    class Meta:
        db_table = "provinces"

    def __str__(self):
        return self.province_name
