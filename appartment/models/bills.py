from django.db import models

from ..constants import StringLength, PaymentStatus, DecimalConfig


class Bill(models.Model):
    bill_id = models.AutoField(primary_key=True)
    bill_month = models.DateTimeField()
    electricity_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    water_amount = models.DecimalField(**DecimalConfig.MONEY, null=True, blank=True)
    additional_service_amount = models.DecimalField(
        **DecimalConfig.MONEY, null=True, blank=True
    )
    total_amount = models.DecimalField(**DecimalConfig.MONEY, null=True, blank=True)
    status = models.CharField(
        max_length=StringLength.SHORT.value,
        choices=PaymentStatus.choices(),
        default=PaymentStatus.UNPAID.value,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    room = models.ForeignKey("Room", on_delete=models.RESTRICT, db_column="room_id")

    class Meta:
        db_table = "bills"

    def __str__(self):
        return f"Bill {self.bill_id} for Room {self.room_id}"
