from django.db import models

from ..constants import StringLength, ServiceType, DecimalConfig


class AdditionalService(models.Model):
    service_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=StringLength.EXTRA_LONG.value)
    type = models.CharField(
        max_length=StringLength.SHORT.value,
        choices=ServiceType.choices(),
        default=ServiceType.PER_ROOM.value,
    )
    description = models.CharField(
        max_length=StringLength.DESCRIPTION.value, null=True, blank=True
    )
    unit_price = models.DecimalField(**DecimalConfig.MONEY)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "additional_services"

    def __str__(self):
        return self.name
