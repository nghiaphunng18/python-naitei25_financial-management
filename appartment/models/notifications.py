from django.db import models
from ..constants import StringLength, NotificationStatus


class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(
        "User",
        on_delete=models.RESTRICT,
        related_name="sent_notifications",
    )
    receiver = models.ForeignKey(
        "User",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="received_notifications",
    )
    title = models.CharField(max_length=StringLength.EXTRA_LONG.value)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=StringLength.SHORT.value,
        choices=NotificationStatus.choices(),
        default=NotificationStatus.UNREAD.value,
    )

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(fields=["sender"]),
            models.Index(fields=["receiver"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.title
