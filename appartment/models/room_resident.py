from django.db import models


class RoomResident(models.Model):
    room_resident_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(
        "Room", on_delete=models.RESTRICT, db_column="room_id", related_name="residents"
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.RESTRICT,
        db_column="user_id",
    )
    move_in_date = models.DateTimeField(auto_now_add=True)
    move_out_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "room_resident"

    def __str__(self):
        return f"Resident {self.user_id} in Room {self.room_id}"
