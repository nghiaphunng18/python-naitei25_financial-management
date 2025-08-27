import time, json
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from payos import PaymentData, ItemData

from django.conf import settings
from appartment.utils.permissions import role_required
from ...models import PaymentHistory, Bill
from ...constants import (
    PaymentTransactionStatus,
    PaymentMethod,
    UserRole,
    WebHookCode,
    PaymentStatus,
    DATE_TIME_FORMAT
)


@role_required(UserRole.RESIDENT.value)
def create_payment(request, bill_id):
    try:
        bill = Bill.objects.get(bill_id=bill_id)
    except Bill.DoesNotExist:
        messages.error(
            request, _("Hóa đơn với ID %(id)s không tồn tại.") % {"id": bill_id}
        )
        return redirect("bill_history")

    # Create order code
    order_code = int(time.time() * 1000)

    # Save payment history with PENDING status
    payment = PaymentHistory.objects.create(
        bill=bill,
        order_code=order_code,
        amount_paid=int(bill.total_amount),
        payment_method=PaymentMethod.BANK_TRANSFER.value,
        transaction_status=PaymentTransactionStatus.PENDING.value,
    )

    item = ItemData(
        name=str(_("Hóa đơn #%(bill_id)s" % {"bill_id": bill.bill_id})),
        quantity=1,
        price=int(bill.total_amount),
    )
    payment_data = PaymentData(
        orderCode=order_code,
        amount=int(bill.total_amount),
        description=str(
            _("Thanh toán hóa đơn #%(bill_id)s" % {"bill_id": bill.bill_id})
        ),
        items=[item],
        cancelUrl=settings.PAYOS_CANCEL_URL,
        returnUrl=settings.PAYOS_RETURN_URL,
    )
    payment_link_response = settings.PAYOS.createPaymentLink(payment_data)

    return redirect(payment_link_response.checkoutUrl)


@csrf_exempt
def payos_webhook(request):
    try:
        payload = json.loads(request.body)
        print(payload)

        data = payload.get("data", {})

        order_code = data.get("orderCode")
        if not order_code:
            return JsonResponse(
                {"success": False, "error": "orderCode missing"}, status=400
            )

        try:
            payment = PaymentHistory.objects.get(order_code=order_code)
            bill = payment.bill
        except PaymentHistory.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Payment not found"}, status=404
            )

        # Identify transaction of code
        code = data.get("code")

        # Parse datetime
        transaction_time = data.get("transactionDateTime")
        if transaction_time:
            try:
                payment.payment_date = datetime.strptime(
                    transaction_time, DATE_TIME_FORMAT
                )
            except ValueError:
                payment.payment_date = timezone.now()
        else:
            payment.payment_date = timezone.now()

        payment.amount_paid = data.get("amount")

        counter_info = {
            "TransactionDescription": data.get("description", ""),
            "BankId": data.get("counterAccountBankId", ""),
            "BankName": data.get("counterAccountBankName", ""),
            "AccountName": data.get("counterAccountName", ""),
            "AccountNumber": data.get("counterAccountNumber", ""),
        }
        notes_str = " | ".join([f"{k}: {v}" for k, v in counter_info.items() if v])
        payment.notes = notes_str

        if code == WebHookCode.SUCCESS.value:
            payment.transaction_status = PaymentTransactionStatus.SUCCESS.value
            bill.status = PaymentStatus.PAID.value
        else:
            payment.transaction_status = PaymentTransactionStatus.FAILED.value
            bill.status = PaymentStatus.UNPAID.value

        bill.save()
        payment.save()

        return JsonResponse({"success": True}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        print("Webhook error:", e)
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@role_required(UserRole.RESIDENT.value)
def payment_success(request):
    messages.success(request, _("Thanh toán thành công!"))
    return redirect("bill_history")


@role_required(UserRole.RESIDENT.value)
def payment_cancel(request):
    messages.error(request, _("Thanh toán thất bại hoặc đã hủy!"))
    return redirect("bill_history")
