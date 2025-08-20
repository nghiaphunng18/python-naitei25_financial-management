import json
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from appartment.models import (
    Room,
    DraftBill,
    Bill,
    RentalPrice,
    SystemSettings,
    BillAdditionalService,
    AdditionalService,
)


class Command(BaseCommand):
    help = "Generates final bills for a specific month from confirmed draft bills."

    def add_arguments(self, parser):
        parser.add_argument(
            "bill_month", type=str, help="The billing month in YYYY-MM format."
        )

    def handle(self, *args, **options):
        month_str = options["bill_month"]
        try:
            bill_month_date = (
                timezone.datetime.strptime(month_str, "%Y-%m").date().replace(day=1)
            )
        except ValueError:
            raise CommandError("Invalid date format. Please use YYYY-MM.")

        self.stdout.write(f"--- Starting final bill generation for {month_str} ---")

        # 1. Tìm tất cả các phòng có đủ 2 HĐ nháp (Điện/Nước và Dịch vụ) đã được 'CONFIRMED'
        confirmed_rooms_qs = (
            DraftBill.objects.filter(
                bill_month=bill_month_date, status=DraftBill.DraftStatus.CONFIRMED
            )
            .values("room")
            .annotate(c=Count("room"))
            .filter(c=2)
        )  # Lọc ra những phòng có đúng 2 HĐ nháp đã confirm

        room_ids_to_process = [item["room"] for item in confirmed_rooms_qs]

        if not room_ids_to_process:
            self.stdout.write(
                self.style.WARNING(
                    "No rooms found with 2 confirmed draft bills for this month."
                )
            )
            return

        self.stdout.write(
            f"Found {len(room_ids_to_process)} rooms to process: {room_ids_to_process}"
        )

        # 2. Xử lý logic chia đều chi phí chung
        # Lấy tổng chi phí chung từ settings
        try:
            common_fee = float(
                SystemSettings.objects.get(
                    setting_key="COMMON_AREA_UTILITY_FEE"
                ).setting_value
            )
            # Giả sử chi phí này được chia đều cho các phòng đã được tạo hóa đơn
            shared_cost_per_room = (
                common_fee / len(room_ids_to_process) if room_ids_to_process else 0
            )
        except SystemSettings.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    "COMMON_AREA_UTILITY_FEE setting not found. Shared costs will be 0."
                )
            )
            shared_cost_per_room = 0

        final_bill_count = 0
        for room_id in room_ids_to_process:
            room = Room.objects.get(pk=room_id)
            self.stdout.write(f"Processing room: {room.description}...")

            # 3. Lấy 2 hóa đơn nháp đã được xác nhận
            ew_draft = DraftBill.objects.get(
                room=room,
                bill_month=bill_month_date,
                draft_type=DraftBill.DraftType.ELECTRIC_WATER,
            )
            services_draft = DraftBill.objects.get(
                room=room,
                bill_month=bill_month_date,
                draft_type=DraftBill.DraftType.SERVICES,
            )

            # 4. Lấy giá thuê phòng áp dụng tại thời điểm đó
            rental_price_obj = (
                RentalPrice.objects.filter(
                    room=room, effective_date__lte=bill_month_date
                )
                .order_by("-effective_date")
                .first()
            )

            if not rental_price_obj:
                self.stdout.write(
                    self.style.ERROR(
                        f"  - SKIPPING: No rental price found for room {room.description}."
                    )
                )
                continue

            # 5. Lấy chi tiết từ các hóa đơn nháp
            ew_details = (
                json.loads(ew_draft.details)
                if isinstance(ew_draft.details, str)
                else ew_draft.details
            )
            services_details = (
                json.loads(services_draft.details)
                if isinstance(services_draft.details, str)
                else services_draft.details
            )

            # 6. Tính toán tổng hóa đơn cuối cùng
            # Tổng tiền = Tiền phòng + Tiền điện nước + Tiền dịch vụ + Tiền chi phí chung đã chia sẻ
            total_amount = (
                rental_price_obj.price
                + ew_draft.total_amount
                + services_draft.total_amount
                + shared_cost_per_room
            )

            # 7. Tạo hoặc cập nhật hóa đơn cuối cùng trong bảng `bills`
            final_bill, created = Bill.objects.update_or_create(
                room=room,
                bill_month=bill_month_date.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
                defaults={
                    "electricity_amount": ew_details.get("electric_cost", 0),
                    "water_amount": ew_details.get("water_cost", 0),
                    "additional_service_amount": services_draft.total_amount,
                    "total_amount": total_amount,
                    "status": "unpaid",  # Hóa đơn cuối cùng luôn bắt đầu là 'unpaid'
                    "due_date": (
                        bill_month_date + relativedelta(months=1, days=14)
                    ),  # Hạn trả là ngày 15 của tháng sau
                },
            )

            # 8. Tạo các bản ghi chi tiết dịch vụ trong `bill_additional_services`
            # Xóa các dịch vụ cũ của hóa đơn này để tránh trùng lặp
            BillAdditionalService.objects.filter(bill=final_bill).delete()
            service_records_to_create = []
            for service_detail in services_details.get("services", []):
                service_records_to_create.append(
                    BillAdditionalService(
                        bill=final_bill,
                        additional_service_id=service_detail.get("service_id"),
                        room=room,
                        service_month=bill_month_date,
                        status="active",
                    )
                )
            BillAdditionalService.objects.bulk_create(service_records_to_create)

            final_bill_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  - Successfully generated final bill #{final_bill.bill_id}."
                )
            )

        self.stdout.write(
            f"--- Finished. Total final bills created/updated: {final_bill_count} ---"
        )
