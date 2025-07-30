from django.db import models

from ..constants import DecimalConfig


class ElectricWaterTotal(models.Model):
    total_id = models.AutoField(primary_key=True)
    summary_for_month = models.DateTimeField()
    total_electricity = models.IntegerField()
    total_water = models.IntegerField()
    electricity_cost = models.DecimalField(**DecimalConfig.MONEY)
    water_cost = models.DecimalField(**DecimalConfig.MONEY)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "electric_water_totals"

    def __str__(self):
        return f"Total for {self.summary_for_month.strftime('%Y-%m')}"
