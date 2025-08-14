from django.db import models

from ..constants import StringLength, BillStatus


class BillAdditionalService(models.Model):
    bill_additional_service_id = models.AutoField(primary_key=True)
    service_month = models.DateTimeField()
    status = models.CharField(
        max_length=StringLength.SHORT.value,
        choices=BillStatus.choices(),
        default=BillStatus.PENDING.value,
    )
    bill = models.ForeignKey(
        "Bill", on_delete=models.RESTRICT, null=True, blank=True, db_column="bill_id"
    )
    additional_service = models.ForeignKey(
        "AdditionalService",
        on_delete=models.RESTRICT,
        db_column="additional_service_id",
    )
    room = models.ForeignKey(
        "Room", on_delete=models.RESTRICT, null=True, blank=True, db_column="room_id"
    )

    class Meta:
        db_table = "bill_additional_services"

    def __str__(self):
        return f"Service {self.additional_service_id} for Bill {self.bill_id}"
