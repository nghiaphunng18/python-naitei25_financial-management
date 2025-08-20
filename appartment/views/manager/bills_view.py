from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import (
    HttpResponseNotAllowed,
    HttpResponseBadRequest,
    HttpResponseNotFound,
)
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum

from ...models import (
    Bill,
    PaymentHistory,
    MonthlyMeterReading,
    SystemSettings,
    DraftBill,
    Room,
    AdditionalService,
    ElectricWaterTotal,
    BillAdditionalService,
    RentalPrice,
)
from ...utils.permissions import RoleRequiredMixin, role_required, RoleRequiredMixin
from ...constants import PaginateNumber, UserRole
from ...forms.manager import bills_form

from dateutil.relativedelta import relativedelta
import json, decimal


class BillingView(RoleRequiredMixin, generic.TemplateView):
    template_name = "manager/bills/billing_main.html"
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # LẤY CÁC THAM SỐ LỌC TỪ URL ---
        month_str = self.request.GET.get("month")
        room_id_param = self.request.GET.get("room")
        status_param = self.request.GET.get("status")

        context["current_status_filter"] = status_param
        month_date = None

        # LẤY QUERYSET GỐC (CHƯA LỌC) ---
        final_bills_qs = (
            Bill.objects.select_related("room")
            .prefetch_related("room__residents__user")
            .order_by("-bill_month")
        )
        draft_ew_bills_qs = (
            DraftBill.objects.filter(draft_type=DraftBill.DraftType.ELECTRIC_WATER)
            .select_related("room")
            .order_by("-bill_month")
        )
        draft_services_bills_qs = (
            DraftBill.objects.filter(draft_type=DraftBill.DraftType.SERVICES)
            .select_related("room")
            .order_by("-bill_month")
        )

        # ÁP DỤNG CÁC BỘ LỌC TUẦN TỰ ---
        if month_str:
            try:
                month_date = timezone.datetime.strptime(month_str, "%Y-%m-%d").date()
                context["selected_month"] = month_date

                final_bills_qs = final_bills_qs.filter(
                    bill_month__year=month_date.year, bill_month__month=month_date.month
                )
                draft_ew_bills_qs = draft_ew_bills_qs.filter(bill_month=month_date)
                draft_services_bills_qs = draft_services_bills_qs.filter(
                    bill_month=month_date
                )
            except (ValueError, TypeError):
                messages.error(self.request, "Định dạng tháng không hợp lệ.")

        if room_id_param:
            final_bills_qs = final_bills_qs.filter(room_id=room_id_param)

        if status_param and status_param != "":
            final_bills_qs = final_bills_qs.filter(status__iexact=status_param)

        # -XỬ LÝ DỮ LIỆU BỔ SUNG VÀ GÁN VÀO CONTEXT ---

        # Xử lý historical_residents cho hóa đơn cuối cùng (trên queryset đã được lọc)
        context["final_bills"] = final_bills_qs
        for bill in context["final_bills"]:
            start_of_bill_month = bill.bill_month.date()
            start_of_next_month = start_of_bill_month + relativedelta(months=1)
            bill.historical_residents = [
                r
                for r in bill.room.residents.all()
                if r.move_in_date.date() < start_of_next_month
                and (
                    r.move_out_date is None
                    or r.move_out_date.date() >= start_of_bill_month
                )
            ]

        context["draft_ew_bills"] = draft_ew_bills_qs
        context["draft_services_bills"] = draft_services_bills_qs
        context["all_rooms"] = Room.objects.all().order_by("room_id")

        # Logic kiểm tra cho Luồng 3
        if month_date and room_id_param:
            try:
                selected_room = context["all_rooms"].get(pk=room_id_param)
                context["selected_room_for_final"] = selected_room
                # ... (logic kiểm tra confirmed_drafts_count không đổi) ...
            except Room.DoesNotExist:
                context["finalization_error"] = _("Phòng không hợp lệ.")

        # Chuẩn bị dữ liệu cho tab nhập liệu nếu có chọn tháng
        if month_date:
            previous_month_date = month_date - relativedelta(months=1)
            context["building_total"] = ElectricWaterTotal.objects.filter(
                summary_for_month__date=month_date
            ).first()

            rooms_data = []
            for room in context["all_rooms"]:
                reading = MonthlyMeterReading.objects.filter(
                    room=room, service_month__date=month_date
                ).first()
                prev_reading = MonthlyMeterReading.objects.filter(
                    room=room, service_month__date=previous_month_date
                ).first()
                draft = draft_ew_bills_qs.filter(room=room).first()

                rooms_data.append(
                    {
                        "room": room,
                        "reading": reading,
                        "prev_reading_index": (
                            prev_reading.electricity_index if prev_reading else 0
                        ),
                        "prev_reading_water_index": (
                            prev_reading.water_index if prev_reading else 0
                        ),
                        "draft": draft,
                    }
                )
            context["rooms_data"] = rooms_data

        form_initial_data = {}
        if month_date:
            form_initial_data["bill_month"] = month_date.strftime("%Y-%m")
        context["adhoc_service_form"] = bills_form.AdhocServiceForm(
            initial=form_initial_data
        )

        return context


class BillDetailView(RoleRequiredMixin, generic.DetailView):
    model = Bill
    template_name = "manager/bills/bills_details.html"
    pk_url_kwarg = "bill_id"
    context_object_name = "bill"
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("room")
            .prefetch_related(
                "room__residents__user", "room__rental_prices", "payment_history"
            )
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bill = self.get_object()

        bill_month_date = bill.bill_month.date()  # SỬA LẠI: Dùng .date()
        start_of_next_month = bill_month_date + relativedelta(months=1)

        all_residents = bill.room.residents.all()
        historical_residents = [
            resident
            for resident in all_residents
            if resident.move_in_date.date() < start_of_next_month
            and (
                resident.move_out_date is None
                or resident.move_out_date.date() >= bill_month_date
            )
        ]
        context["historical_residents"] = historical_residents

        applicable_price = None
        rental_prices = bill.room.rental_prices.order_by("-effective_date")
        for price in rental_prices:

            if price.effective_date.date() <= bill_month_date:
                applicable_price = price
                break
        context["rental_price"] = applicable_price
        return context


class CreateFinalBillView(RoleRequiredMixin, generic.View):
    template_name = "manager/bills/create_final_bill.html"
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def get(self, request, *args, **kwargs):
        # GET request: Hiển thị form trống ban đầu
        context = {
            "page_title": _("Tạo Hóa đơn Tổng hợp Thủ công"),
            "rooms": Room.objects.filter(status="occupied").order_by("room_id"),
            "step": 1,  # Đánh dấu đây là bước 1
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # POST request: Xử lý sau khi người dùng nhấn "Kiểm tra điều kiện"
        room_id = request.POST.get("room")
        month_str = request.POST.get("month")
        context = {
            "page_title": _("Tạo Hóa đơn Tổng hợp Thủ công"),
            "rooms": Room.objects.filter(status="occupied").order_by("room_id"),
            "selected_room_id": room_id,
            "selected_month_str": month_str,
            "step": 2,  # Đánh dấu đây là bước 2
        }

        if not all([room_id, month_str]):
            messages.error(request, _("Vui lòng chọn phòng và tháng."))
            return render(request, self.template_name, context)

        try:
            month_date = timezone.datetime.strptime(month_str, "%Y-%m-%d").date()
            room = Room.objects.get(pk=room_id)
        except (ValueError, TypeError, Room.DoesNotExist):
            messages.error(request, _("Phòng hoặc tháng không hợp lệ."))
            return render(request, self.template_name, context)

        # Kiểm tra HĐ nháp đã được xác nhận
        confirmed_drafts = DraftBill.objects.filter(
            room=room, bill_month=month_date, status=DraftBill.DraftStatus.CONFIRMED
        )

        ew_draft = confirmed_drafts.filter(
            draft_type=DraftBill.DraftType.ELECTRIC_WATER
        ).first()
        services_draft = confirmed_drafts.filter(
            draft_type=DraftBill.DraftType.SERVICES
        ).first()

        context["ew_draft"] = ew_draft
        context["services_draft"] = services_draft

        if ew_draft and services_draft:
            # Nếu đủ điều kiện, lấy thêm giá thuê để hiển thị tổng dự kiến
            rental_price_obj = (
                RentalPrice.objects.filter(room=room, effective_date__lte=month_date)
                .order_by("-effective_date")
                .first()
            )
            context["rental_price"] = rental_price_obj
            if rental_price_obj:
                context["is_ready"] = True
                total_amount = (
                    rental_price_obj.price
                    + ew_draft.total_amount
                    + services_draft.total_amount
                )
                context["estimated_total"] = total_amount
            else:
                messages.error(
                    request,
                    _("Không tìm thấy giá thuê cho phòng %(description)s.")
                    % {"description": room.description},
                )
                context["is_ready"] = False
        else:
            context["is_ready"] = False
            if not ew_draft:
                messages.warning(
                    request, _("Hóa đơn Điện/Nước nháp chưa được xác nhận.")
                )
            if not services_draft:
                messages.warning(request, _("Hóa đơn Dịch vụ nháp chưa được xác nhận."))

        return render(request, self.template_name, context)


# class BillUpdateView(RoleRequiredMixin, generic.UpdateView):
#     model = Bill
#     form_class = bills_form.BillForm
#     template_name = "manager/bills/bill_form.html"
#     pk_url_kwarg = "bill_id"
#     context_object_name = "bill"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["page_title"] = _(f"Cập nhật Hóa Đơn #{self.object.bill_id}")
#         context["adhoc_service_form"] = bills_form.AdhocServiceForm()
#         return context

#     def get_success_url(self):
#         return reverse("bill", kwargs={"bill_id": self.object.pk})


class BillDeleteView(RoleRequiredMixin, generic.DeleteView):
    model = Bill
    success_url = reverse_lazy("bills_list")
    pk_url_kwarg = "bill_id"
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def get(self, request, *args, **kwargs):
        # Chặn truy cập GET, chỉ cho phép POST
        return HttpResponseNotAllowed(["POST"])

    def post(self, request, *args, **kwargs):
        bill = self.get_object()

        # Xóa các dữ liệu liên quan (nếu dùng RESTRICT trong ForeignKey)
        PaymentHistory.objects.filter(bill=bill).delete()
        BillAdditionalService.objects.filter(bill=bill).delete()

        # Xóa chính bill
        bill.delete()

        messages.success(request, _("Đã xóa hóa đơn và các dữ liệu liên quan."))
        return redirect(self.success_url)


@role_required(UserRole.APARTMENT_MANAGER.value)
@require_POST
def confirm_payment_view(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    if bill.status.upper() != "PAID":
        bill.status = "paid"  # Hoặc "PAID" tùy theo giá trị bạn muốn lưu
        bill.save()
        PaymentHistory.objects.create(
            bill=bill,
            amount_paid=bill.total_amount,
            payment_method="CASH",  # Hoặc "BANK_TRANSFER"
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


class BuildingUtilityTotalView(RoleRequiredMixin, generic.View):
    """
    View để quản lý nhập tổng điện/nước tiêu thụ của cả tòa nhà.
    """

    template_name = "manager/bills/utility_totals.html"
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def get(self, request, *args, **kwargs):
        totals = ElectricWaterTotal.objects.all().order_by("-summary_for_month")
        context = {"totals": totals}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # POST request: Xử lý việc thêm/cập nhật bản ghi tổng mới
        month_str = request.POST.get("summary_for_month")
        total_electricity_str = request.POST.get("total_electricity")
        total_water_str = request.POST.get("total_water")
        electricity_cost_str = request.POST.get("electricity_cost")
        water_cost_str = request.POST.get("water_cost")

        # Kiểm tra xem người dùng có nhập đủ các trường không
        if not all(
            [
                month_str,
                total_electricity_str,
                total_water_str,
                electricity_cost_str,
                water_cost_str,
            ]
        ):
            messages.error(request, _("Vui lòng điền đầy đủ tất cả các trường."))
            return redirect("utility_totals")

        try:
            # Chuyển đổi dữ liệu sang đúng kiểu
            month_date = (
                timezone.datetime.strptime(month_str, "%Y-%m-%d").date().replace(day=1)
            )
            defaults_data = {
                "total_electricity": decimal.Decimal(total_electricity_str),
                "total_water": decimal.Decimal(total_water_str),
                "electricity_cost": decimal.Decimal(electricity_cost_str),
                "water_cost": decimal.Decimal(water_cost_str),
            }
        except (ValueError, TypeError, decimal.InvalidOperation):
            messages.error(request, _("Định dạng số hoặc ngày tháng không hợp lệ."))
            return redirect("utility_totals")

        # Dùng update_or_create để tạo mới nếu chưa có, hoặc cập nhật nếu đã có
        ElectricWaterTotal.objects.update_or_create(
            summary_for_month=month_date, defaults=defaults_data
        )

        messages.success(
            request,
            _(f"Đã lưu thành công tổng cho tháng {month_date.strftime('%m/%Y')}."),
        )
        return redirect("utility_totals")


class SaveMeterReadingView(RoleRequiredMixin, generic.View):
    """
    Xử lý việc quản lý nhập, xác thực và lưu chỉ số điện/nước cho một phòng cụ thể.
    """

    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def post(self, request, room_id):
        #  LẤY VÀ KIỂM TRA DỮ LIỆU ĐẦU VÀO ---
        room_to_update = get_object_or_404(Room, pk=room_id)
        month_str = request.POST.get("month")

        # Chuyển hướng về trang chính nếu không có tháng
        # Sửa lại để trỏ về bills_list thay vì bills_list
        redirect_url = reverse("bills_list")
        if not month_str:
            messages.error(
                request, _("Lỗi: Thiếu thông tin tháng. Vui lòng chọn lại tháng.")
            )
            return redirect(redirect_url)

        redirect_url_with_month = f"{redirect_url}?month={month_str}"

        try:
            new_electricity_index = decimal.Decimal(
                request.POST.get("electricity_index")
            )
            new_water_index = decimal.Decimal(request.POST.get("water_index"))
            month_date = timezone.datetime.strptime(month_str, "%Y-%m-%d").date()
        except (ValueError, TypeError, decimal.InvalidOperation):
            messages.error(request, _("Dữ liệu nhập vào (số điện/nước) không hợp lệ."))
            return redirect(redirect_url_with_month)

        previous_month_date = month_date - relativedelta(months=1)

        # LẤY DỮ LIỆU NỀN TẢNG ĐỂ XÁC THỰC ---
        building_total = ElectricWaterTotal.objects.filter(
            summary_for_month__date=month_date
        ).first()
        if not building_total:
            messages.error(
                request,
                _(
                    f"Lỗi: Chưa nhập tổng của tòa nhà cho tháng {month_date.strftime('%m/%Y')}."
                ),
            )
            return redirect(redirect_url_with_month)

        # Lấy TẤT CẢ chỉ số của tháng trước và tháng này
        previous_readings = MonthlyMeterReading.objects.filter(
            service_month__date=previous_month_date
        )
        current_readings = MonthlyMeterReading.objects.filter(
            service_month__date=month_date
        )

        # Chuyển thành dạng dictionary để tra cứu nhanh, tránh N+1 query
        previous_readings_map = {r.room_id: r for r in previous_readings}
        current_readings_map = {r.room_id: r for r in current_readings}
        # Cập nhật (giả lập) chỉ số mới cho phòng đang được lưu
        # để tính toán tổng tiêu thụ "nếu" lưu thành công
        current_readings_map[room_to_update.room_id] = MonthlyMeterReading(
            electricity_index=new_electricity_index, water_index=new_water_index
        )

        # tính tổng tiêu thụ của TẤT CẢ các phòng dựa trên dữ liệu mới nhất
        total_electric_consumption_all_rooms = 0
        total_water_consumption_all_rooms = 0

        for room_id, current_reading in current_readings_map.items():
            prev_reading = previous_readings_map.get(room_id)
            old_electric = prev_reading.electricity_index if prev_reading else 0
            old_water = prev_reading.water_index if prev_reading else 0

            # Kiểm tra chỉ số mới phải lớn hơn hoặc bằng chỉ số cũ
            if (
                current_reading.electricity_index < old_electric
                or current_reading.water_index < old_water
            ):
                messages.error(
                    request,
                    _(
                        f"Lỗi: Chỉ số mới của phòng {room_id} không thể nhỏ hơn chỉ số cũ."
                    ),
                )
                return redirect(redirect_url_with_month)

            total_electric_consumption_all_rooms += (
                current_reading.electricity_index - old_electric
            )
            total_water_consumption_all_rooms += current_reading.water_index - old_water

        # Xác thực tổng điện
        if total_electric_consumption_all_rooms > building_total.total_electricity:
            messages.error(
                request,
                _(
                    f"Lỗi: Tổng số điện tiêu thụ của các phòng ({total_electric_consumption_all_rooms} kWh) sẽ vượt quá tổng của tòa nhà ({building_total.total_electricity} kWh)."
                ),
            )
            return redirect(redirect_url_with_month)

        # Xác thực tổng nước
        if total_water_consumption_all_rooms > building_total.total_water:
            messages.error(
                request,
                _(
                    f"Lỗi: Tổng số nước tiêu thụ của các phòng ({total_water_consumption_all_rooms} m³) sẽ vượt quá tổng của tòa nhà ({building_total.total_water} m³)."
                ),
            )
            return redirect(redirect_url_with_month)

        # LƯU DỮ LIỆU NẾU HỢP LỆ ---

        # Lưu chỉ số mới vào monthly_meter_readings
        MonthlyMeterReading.objects.update_or_create(
            room=room_to_update,
            service_month=month_date,
            defaults={
                "electricity_index": new_electricity_index,
                "water_index": new_water_index,
                "status": "recorded",
            },
        )

        # Tính toán chi phí và tạo hóa đơn nháp
        prev_reading_this_room = previous_readings_map.get(room_to_update.room_id)
        old_electric_index_this_room = (
            prev_reading_this_room.electricity_index if prev_reading_this_room else 0
        )
        old_water_index_this_room = (
            prev_reading_this_room.water_index if prev_reading_this_room else 0
        )

        electric_consumption = new_electricity_index - old_electric_index_this_room
        water_consumption = new_water_index - old_water_index_this_room

        electric_price = decimal.Decimal(
            SystemSettings.objects.get(
                setting_key="ELECTRICITY_UNIT_PRICE"
            ).setting_value
        )
        water_price = decimal.Decimal(
            SystemSettings.objects.get(setting_key="WATER_UNIT_PRICE").setting_value
        )

        electric_cost = electric_consumption * electric_price
        water_cost = water_consumption * water_price
        total_ew_cost = electric_cost + water_cost

        details_data = {
            "old_electric_index": float(old_electric_index_this_room),
            "new_electric_index": float(new_electricity_index),
            "electric_consumption": float(electric_consumption),
            "electric_unit_price": float(electric_price),
            "electric_cost": float(electric_cost),
            "old_water_index": float(old_water_index_this_room),
            "new_water_index": float(new_water_index),
            "water_consumption": float(water_consumption),
            "water_unit_price": float(water_price),
            "water_cost": float(water_cost),
        }

        DraftBill.objects.update_or_create(
            room=room_to_update,
            bill_month=month_date,
            draft_type=DraftBill.DraftType.ELECTRIC_WATER,
            defaults={
                "total_amount": total_ew_cost,
                "details": details_data,
                "status": DraftBill.DraftStatus.SENT,
            },
        )

        messages.success(
            request,
            _(f"Đã lưu chỉ số thành công cho phòng {room_to_update.description}."),
        )
        return redirect(redirect_url_with_month)


class DraftBillDetailView(RoleRequiredMixin, generic.DetailView):
    model = DraftBill
    template_name = "manager/bills/draft_bill_detail.html"
    context_object_name = "draft_bill"
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Truyền tất cả các lựa chọn status vào template
        context["status_choices"] = DraftBill.DraftStatus.choices
        return context


@role_required(UserRole.APARTMENT_MANAGER.value)
@require_POST
def update_draft_bill_status_view(request, pk):
    draft_bill = get_object_or_404(DraftBill, pk=pk)
    new_status = request.POST.get("status")

    # Kiểm tra xem status mới có hợp lệ không
    valid_statuses = [status.value for status in DraftBill.DraftStatus]
    if new_status in valid_statuses:
        draft_bill.status = new_status
        if new_status == DraftBill.DraftStatus.CONFIRMED:
            draft_bill.confirmed_at = timezone.now()
        draft_bill.save()
        messages.success(request, _("Đã cập nhật trạng thái hóa đơn nháp thành công."))
    else:
        messages.error(request, _("Trạng thái không hợp lệ."))

    return redirect("draft_bill_detail", pk=draft_bill.pk)


# tạo một hàm helper để tái sử dụng logic này
def get_historical_residents(room, bill_month):
    start_of_next_month = bill_month + relativedelta(months=1)
    return [
        res
        for res in room.residents.all()
        if res.move_in_date.date() < start_of_next_month
        and (res.move_out_date is None or res.move_out_date.date() >= bill_month)
    ]


class AddAdhocServiceView(RoleRequiredMixin, generic.View):
    """
    Xử lý việc thêm thủ công một dịch vụ lẻ vào hóa đơn nháp của một phòng.
    """

    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def post(self, request, *args, **kwargs):
        form = bills_form.AdhocServiceForm(request.POST)

        # chuẩn bị URL để redirect, kể cả khi lỗi
        month_str_from_post = request.POST.get("bill_month", "")  # Format YYYY-MM
        redirect_url = reverse("bills_list")
        if month_str_from_post:
            # giữ lại tháng đã chọn trên URL khi có lỗi
            redirect_url = f"{redirect_url}?month={month_str_from_post}-01"

        if form.is_valid():
            room = form.cleaned_data["room"]
            service_to_add = form.cleaned_data["service"]

            # Chuyển đổi YYYY-MM từ form thành đối tượng date
            try:
                bill_month = (
                    timezone.datetime.strptime(
                        form.cleaned_data["bill_month"], "%Y-%m-%d"
                    )
                    .date()
                    .replace(day=1)
                )
            except (ValueError, TypeError):
                messages.error(request, _("Định dạng tháng trong form không hợp lệ."))
                return redirect(redirect_url)

            # Tìm hoặc tạo hóa đơn nháp dịch vụ cho phòng và tháng đó
            draft_bill, created = DraftBill.objects.get_or_create(
                room=room,
                bill_month=bill_month,
                draft_type=DraftBill.DraftType.SERVICES,
                defaults={
                    "total_amount": 0,
                    "details": {"services": []},
                    "status": DraftBill.DraftStatus.DRAFT,
                },
            )

            # Kiểm tra dịch vụ đã tồn tại trong hóa đơn nháp chưa
            if any(
                s.get("service_id") == service_to_add.pk
                for s in draft_bill.details.get("services", [])
            ):
                messages.warning(
                    request,
                    _(f"Dịch vụ '{service_to_add.name}' đã có trong hóa đơn nháp này."),
                )
                return redirect(
                    f"{reverse('bills_list')}?month={bill_month.strftime('%Y-%m-%d')}"
                )

            # Tính toán chi phí cho dịch vụ mới
            num_residents = len(get_historical_residents(room, bill_month))
            cost = 0
            if service_to_add.type.upper() == "PER_ROOM":
                cost = service_to_add.unit_price
            elif service_to_add.type.upper() == "PER_PERSON" and num_residents > 0:
                cost = service_to_add.unit_price * num_residents

            # Cập nhật hóa đơn nháp
            draft_bill.details["services"].append(
                {
                    "service_id": service_to_add.pk,
                    "name": service_to_add.name,
                    "cost": float(cost),
                    "type": service_to_add.type,
                    "num_residents": (
                        num_residents
                        if service_to_add.type.upper() == "PER_PERSON"
                        else None
                    ),
                    "unit_price": float(service_to_add.unit_price),
                }
            )
            draft_bill.total_amount += decimal.Decimal(cost)
            draft_bill.save()

            messages.success(
                request,
                _(
                    f"Đã thêm dịch vụ '{service_to_add.name}' vào HĐ nháp của phòng {room.description}."
                ),
            )

            # Chuyển hướng khi thành công
            return redirect(
                _(f"{reverse('bills_list')}?month={bill_month.strftime('%Y-%m-%d')}")
            )
        else:
            # Khi form KHÔNG hợp lệ
            # Lấy lỗi đầu tiên để hiển thị
            first_error = next(iter(form.errors.values()))[0]
            messages.error(request, f"Dữ liệu không hợp lệ: {first_error}")
            return redirect(redirect_url)


class GenerateFinalBillView(RoleRequiredMixin, generic.View):
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def post(self, request, *args, **kwargs):
        month_str = request.POST.get("month")
        room_id = request.POST.get("room_id")

        # ... (Thêm validation cho các input) ...
        print("DEBUG: room_id =", room_id)
        print("DEBUG: month_str =", month_str)

        if not room_id:
            return HttpResponseBadRequest(_("Thiếu room_id"))

        # Kiểm tra room có tồn tại trong DB không
        if not Room.objects.filter(pk=room_id).exists():
            print(_("Room không tồn tại trong DB!"))
            return HttpResponseNotFound(_("Room không tồn tại"))

        month_date = timezone.datetime.strptime(month_str, "%Y-%m-%d").date()
        room = get_object_or_404(Room, pk=room_id)
        redirect_url = f"{reverse('bills_list')}?month={month_str}"

        # Kiểm tra lại lần cuối trước khi tạo
        confirmed_drafts = DraftBill.objects.filter(
            room=room, bill_month=month_date, status=DraftBill.DraftStatus.CONFIRMED
        )

        if confirmed_drafts.count() != 2:
            messages.error(
                request,
                _(
                    f"Lỗi: Phòng {room.description} chưa có đủ 2 HĐ nháp được xác nhận cho tháng này."
                ),
            )
            return redirect(redirect_url)

        # ... (Toàn bộ logic của Luồng 3) ...
        ew_draft = confirmed_drafts.get(draft_type=DraftBill.DraftType.ELECTRIC_WATER)
        services_draft = confirmed_drafts.get(draft_type=DraftBill.DraftType.SERVICES)
        rental_price_obj = (
            RentalPrice.objects.filter(room=room, effective_date__lte=month_date)
            .order_by("-effective_date")
            .first()
        )

        if not rental_price_obj:
            messages.error(
                request,
                _(f"Lỗi: Không tìm thấy giá thuê cho phòng {room.description}."),
            )
            return redirect(redirect_url)

        # Tính toán tổng tiền
        total_amount = (
            rental_price_obj.price + ew_draft.total_amount + services_draft.total_amount
        )
        # (Bạn có thể thêm logic tính chi phí chung ở đây)

        # Tạo hóa đơn cuối cùng
        final_bill, created = Bill.objects.update_or_create(
            room=room,
            bill_month=month_date,
            defaults={
                "electricity_amount": ew_draft.details.get("electric_cost", 0),
                "water_amount": ew_draft.details.get("water_cost", 0),
                "additional_service_amount": services_draft.total_amount,
                "total_amount": total_amount,
                "status": "unpaid",
                "due_date": (month_date + relativedelta(months=1, days=14)),
            },
        )

        # Tạo chi tiết dịch vụ
        BillAdditionalService.objects.filter(bill=final_bill).delete()
        service_records_to_create = [
            BillAdditionalService(
                bill=final_bill,
                additional_service_id=s["service_id"],
                room=room,
                service_month=month_date,
                status="active",
            )
            for s in services_draft.details.get("services", [])
        ]
        BillAdditionalService.objects.bulk_create(service_records_to_create)

        messages.success(
            request, _(f"Đã tạo HĐ cuối cùng thành công cho phòng {room.description}.")
        )
        return redirect(redirect_url)
