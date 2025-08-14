from django.db import models

from ..constants import StringLength, ElectricWaterStatus


class MonthlyMeterReading(models.Model):
    service_id = models.AutoField(primary_key=True)
    room = models.ForeignKey("Room", on_delete=models.RESTRICT, db_column="room_id")
    service_month = models.DateTimeField()
    electricity_index = models.IntegerField(null=True, blank=True)
    water_index = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=StringLength.SHORT.value,
        choices=ElectricWaterStatus.choices(),
        default=ElectricWaterStatus.PENDING.value,
    )

    class Meta:
        pass
        db_table = "monthly_meter_readings"

    def __str__(self):
        return (
            f"Service for Room {self.room_id} in {self.service_month.strftime('%Y-%m')}"
        )
