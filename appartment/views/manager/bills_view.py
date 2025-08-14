from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from appartment.models import (
    bills,
    PaymentHistory,
    MonthlyMeterReading,
    SystemSettings,
    DraftBill,
    rooms,
)
from appartment.utils.permissions import StaffRequiredMixin, role_required
from appartment.constants import PaginateNumber
from dateutil.relativedelta import relativedelta
from appartment.forms.manager import bills_form
import json
from ...constants import UserRole


class bills_list_view(StaffRequiredMixin, generic.ListView):
    model = bills.Bill
    template_name = "manager/bills/bills_list.html"
    context_object_name = "bills_list"
    paginate_by = PaginateNumber.P_SHORT.value

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("room")
            .prefetch_related("room__residents__user")
            .order_by("-bill_month")
        )
        status_param = self.request.GET.get("status")

        if status_param in ["paid", "unpaid", "overdue"]:
            queryset = queryset.filter(status=status_param)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bills_list = context.get("bills_list", [])

        for bill in bills_list:
            all_residents = bill.room.residents.all()

            # fillter resident
            start_of_bill_month = bill.bill_month
            # Tính ngày đầu tiên của tháng kế tiếp
            start_of_next_month = bill.bill_month + relativedelta(months=1)

            historical_residents = [
                resident
                for resident in all_residents
                if resident.move_in_date < start_of_next_month
                and (
                    resident.move_out_date is None
                    or resident.move_out_date >= start_of_bill_month
                )
            ]

            bill.historical_residents = historical_residents

        return context


class BillDetailView(StaffRequiredMixin, generic.DetailView):
    model = bills.Bill
    template_name = "manager/bills/bills_details.html"
    pk_url_kwarg = "bill_id"
    context_object_name = "bill"

    def get_queryset(self):
        """
        Tối ưu hóa truy vấn bằng cách tải trước tất cả các dữ liệu liên quan.
        Việc này giúp tránh lỗi N+1 query và tăng hiệu năng đáng kể.
        """
        queryset = (
            super()
            .get_queryset()
            .select_related("room")
            .prefetch_related(
                "room__residents__user",  # Lấy thông tin người ở: Bill -> Room -> RoomResident -> User
                "room__rental_prices",  # Lấy các mức giá thuê của phòng
                "payment_history",  # Lấy lịch sử thanh toán của hóa đơn
            )
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bill = self.get_object()

        # filter resident
        all_residents = bill.room.residents.all()
        start_of_bill_month = bill.bill_month
        start_of_next_month = bill.bill_month + relativedelta(months=1)

        historical_residents = [
            resident
            for resident in all_residents
            if resident.move_in_date < start_of_next_month
            and (
                resident.move_out_date is None
                or resident.move_out_date >= start_of_bill_month
            )
        ]
        context["historical_residents"] = historical_residents

        # price rental
        applicable_price = None
        rental_prices = bill.room.rental_prices.order_by("-effective_date")
        for price in rental_prices:
            if price.effective_date <= bill.bill_month:
                applicable_price = price
                break
        context["rental_price"] = applicable_price

        return context


class BillCreateView(StaffRequiredMixin, generic.CreateView):
    model = bills.Bill
    form_class = bills_form.BillForm
    template_name = "manager/bills/bill_form.html"
    success_url = reverse_lazy("bills_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Tạo Hóa Đơn Mới")
        return context


class BillUpdateView(StaffRequiredMixin, generic.UpdateView):
    model = bills.Bill
    form_class = bills_form.BillForm
    template_name = "manager/bills/bill_form.html"
    pk_url_kwarg = "bill_id"
    context_object_name = "bill"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _(f"Cập nhật Hóa Đơn #{self.object.bill_id}")
        return context

    def get_success_url(self):
        return reverse("bill", kwargs={"bill_id": self.object.pk})


class BillDeleteView(StaffRequiredMixin, generic.DeleteView):
    model = bills.Bill
    success_url = reverse_lazy("bills_list")
    pk_url_kwarg = "bill_id"

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


@role_required(UserRole.APARTMENT_MANAGER.value)
@require_POST
def confirm_payment_view(request, bill_id):
    bill = get_object_or_404(bills.Bill, pk=bill_id)

    if bill.status != "paid":
        # bill status upsdate
        bill.status = "paid"
        bill.save()

        # create payment history
        PaymentHistory.objects.create(
            bill=bill,
            amount_paid=bill.total_amount,
            payment_method="CASH",
            notes=_(f"Thanh toán được xác nhận bởi {request.user.full_name}."),
            payment_date=timezone.now(),
            processed_by=request.user,
        )

        messages.success(
            request,
            _(f"Đã xác nhận thanh toán thành công cho hóa đơn #{bill.bill_id}."),
        )
    else:
        messages.warning(
            request, _(f"Hóa đơn #{bill.bill_id} đã được thanh toán trước đó.")
        )

    return redirect("bill", bill_id=bill.pk)


class BillPrintView(BillDetailView):
    template_name = "manager/bills/bill_print.html"
