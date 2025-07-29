from django.db import models

from ..constants import StringLength, NotificationStatus

class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    room = models.ForeignKey('Room', on_delete=models.RESTRICT, null=True, blank=True, db_column='room_id')
    user = models.ForeignKey('User', on_delete=models.RESTRICT, null=True, blank=True, db_column='user_id')
    title = models.CharField(max_length=StringLength.EXTRA_LONG.value)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=StringLength.SHORT.value,
        choices=NotificationStatus.choices(),
        default=NotificationStatus.UNREAD.value
    )

    class Meta:
        db_table = 'notifications'

    def __str__(self):
        return self.title
