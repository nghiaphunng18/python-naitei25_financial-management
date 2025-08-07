from django.db import models

from django.utils import timezone

from ..constants import DecimalConfig


class RentalPrice(models.Model):
    rental_price_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(
        "Room",
        on_delete=models.RESTRICT,
        db_column="room_id",
        related_name="rental_prices",
    )
    price = models.DecimalField(**DecimalConfig.MONEY)
    effective_date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "rental_prices"

    def __str__(self):
        return f"Price {self.price} for Room {self.room_id}"
