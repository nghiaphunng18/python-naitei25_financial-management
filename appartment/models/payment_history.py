from django.db import models

from ..constants import (
    StringLength,
    PaymentMethod,
    DecimalConfig,
    PaymentTransactionStatus,
)


class PaymentHistory(models.Model):
    payment_id = models.AutoField(primary_key=True)
    bill = models.ForeignKey(
        "Bill",
        on_delete=models.RESTRICT,
        db_column="bill_id",
        related_name="payment_history",
        null=True,
        blank=True,
    )
    order_code = models.BigIntegerField(null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
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
    transaction_status = models.CharField(
        max_length=StringLength.SHORT.value,
        choices=PaymentTransactionStatus.choices(),
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        db_table = "payment_history"

    def __str__(self):
        return f"Payment {self.payment_id} for Bill {self.bill_id}"
