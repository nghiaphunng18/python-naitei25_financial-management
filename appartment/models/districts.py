from django.db import models

from ..constants import StringLength


class District(models.Model):
    district_id = models.AutoField(primary_key=True)
    district_name = models.CharField(max_length=StringLength.MEDIUM.value)
    district_code = models.CharField(max_length=StringLength.MEDIUM.value)
    province = models.ForeignKey(
        "Province", on_delete=models.RESTRICT, db_column="province_id"
    )

    class Meta:
        db_table = "districts"

    def __str__(self):
        return self.district_name
