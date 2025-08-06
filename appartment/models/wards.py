from django.db import models

from ..constants import StringLength


class Ward(models.Model):
    ward_id = models.AutoField(primary_key=True)
    ward_name = models.CharField(max_length=StringLength.MEDIUM.value)
    ward_code = models.CharField(max_length=StringLength.MEDIUM.value)
    district = models.ForeignKey(
        "District", on_delete=models.RESTRICT, db_column="district_id"
    )

    class Meta:
        db_table = "wards"

    def __str__(self):
        return self.ward_name
