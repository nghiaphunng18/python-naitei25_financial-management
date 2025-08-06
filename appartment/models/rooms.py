from django.db import models

from ..constants import StringLength, RoomStatus


class Room(models.Model):
    room_id = models.CharField(max_length=StringLength.SHORT.value, primary_key=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=StringLength.SHORT.value,
        choices=RoomStatus.choices(),
        default=RoomStatus.AVAILABLE.value,
    )
    max_occupants = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rooms"

    def __str__(self):
        return self.room_id
