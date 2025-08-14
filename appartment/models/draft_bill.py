from django.db import models
from ..constants import StringLength


# Model cho các hóa đơn nháp
class DraftBill(models.Model):
    class DraftType(models.TextChoices):
        ELECTRIC_WATER = "ELECTRIC_WATER", "Điện & Nước"
        SERVICES = "SERVICES", "Dịch vụ"

    class DraftStatus(models.TextChoices):
        DRAFT = "DRAFT", "Nháp"
        SENT = "SENT", "Đã gửi"
        CONFIRMED = "CONFIRMED", "Đã xác nhận"
        REJECTED = "REJECTED", "Đã từ chối"

    draft_bill_id = models.AutoField(primary_key=True)
    room = models.ForeignKey("Room", on_delete=models.CASCADE)
    bill_month = models.DateField()
    draft_type = models.CharField(
        max_length=StringLength.SHORT.value, choices=DraftType.choices
    )
    status = models.CharField(
        max_length=StringLength.SHORT.value,
        choices=DraftStatus.choices,
        default=DraftStatus.DRAFT,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    details = models.JSONField(null=True, blank=True)  # Lưu chi tiết tính toán
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Draft Bill for {self.room} - {self.bill_month.strftime('%Y-%m')} ({self.get_draft_type_display()})"

    class Meta:
        db_table = "draft_bills"  # Giữ tên bảng giống như SQL
        unique_together = (
            "room",
            "bill_month",
            "draft_type",
        )  # Đảm bảo không có 2 hóa đơn nháp cùng loại trong cùng 1 tháng cho 1 phòng
