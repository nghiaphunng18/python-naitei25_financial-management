from django.db import models

from ..constants import StringLength, PaymentMethod, DecimalConfig


class PaymentHistory(models.Model):
    payment_id = models.AutoField(primary_key=True)
    bill = models.ForeignKey(
        "Bill",
        on_delete=models.RESTRICT,
        db_column="bill_id",
        related_name="payment_history",
    )
    payment_date = models.DateTimeField()
    amount_paid = models.DecimalField(**DecimalConfig.MONEY)
    payment_method = models.CharField(
        max_length=StringLength.SHORT.value, choices=PaymentMethod.choices()
    )
    processed_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="processed_by",
    )
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "payment_history"

    def __str__(self):
        return f"Payment {self.payment_id} for Bill {self.bill_id}"
