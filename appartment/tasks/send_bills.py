from datetime import date

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from appartment.models import Bill, RoomResident
from appartment.constants import BILL_SEND_DAYS


def send_monthly_bills():
    today = date.today()

    if today.day not in BILL_SEND_DAYS:
        return

    # Lấy tất cả bills của tháng hiện tại
    bills = Bill.objects.filter(
        bill_month__month=today.month,
        bill_month__year=today.year,
    )

    for bill in bills:
        room = bill.room
        # lấy resident đang ở trong phòng (chưa move out)
        residents = RoomResident.objects.filter(room=room, move_out_date__isnull=True)

        for resident in residents:
            user = resident.user
            subject = (
                f"Hóa đơn tiền phòng {today.month}/{today.year} - Phòng {room.room_id}"
            )
            from_email = None
            to_email = [user.email]

            text_content = f"""
            Hóa đơn phòng {bill.room.room_id} tháng {today.month}/{today.year}:
            Điện: {bill.electricity_amount} VND
            Nước: {bill.water_amount} VND
            Dịch vụ khác: {bill.additional_service_amount} VND
            Tổng: {bill.total_amount} VND
            Hạn thanh toán: {bill.due_date.strftime('%d/%m/%Y') if bill.due_date else 'N/A'}
            """

            html_content = render_to_string(
                "emails/auto_bill.html",
                {
                    "user_name": user.full_name,
                    "room": bill.room.room_id,
                    "month": today.month,
                    "year": today.year,
                    "electricity": bill.electricity_amount or 0,
                    "water": bill.water_amount or 0,
                    "services": bill.additional_service_amount or 0,
                    "total": bill.total_amount or 0,
                    "due_date": (
                        bill.due_date.strftime("%d/%m/%Y") if bill.due_date else "N/A"
                    ),
                },
            )

            msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
