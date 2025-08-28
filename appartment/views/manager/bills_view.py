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
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
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
    RoomResident,
    Notification,
)
from ...utils.permissions import RoleRequiredMixin, role_required
from ...constants import PaymentStatus, UserRole, YEAR_MONTH_DAY_FORMAT
from ...forms.manager import bills_form
from dateutil.relativedelta import relativedelta
import json, decimal
from datetime import datetime, date
from collections import Counter


class BillingWorkspaceView(RoleRequiredMixin, generic.TemplateView):
    template_name = "manager/bills/billing_workspace.html"
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- LẤY CÁC THAM SỐ LỌC ---
        month_str = self.request.GET.get(
            "month", timezone.now().strftime(YEAR_MONTH_DAY_FORMAT)
        )
        search_query = self.request.GET.get("q", "")
        billing_status_filter = self.request.GET.get("billing_status", "")

        try:
            month_date = (
                timezone.datetime.strptime(month_str, YEAR_MONTH_DAY_FORMAT)
                .date()
                .replace(day=1)
            )
        except (ValueError, TypeError):
            month_date = timezone.now().date().replace(day=1)
            messages.error(
                self.request,
                _("Định dạng tháng trên URL không hợp lệ, đã quay về tháng hiện tại."),
            )

        context["selected_month"] = month_date
        context["search_query"] = search_query
        context["billing_status_filter"] = billing_status_filter
        previous_month_date = month_date - relativedelta(months=1)
        start_of_bill_month = month_date
        start_of_next_month = month_date + relativedelta(months=1)

        # --- LẤY VÀ LỌC DANH SÁCH PHÒNG ---
        rooms_qs = (
            Room.objects.prefetch_related("residents__user")
            .filter(
                # Điều kiện 1: Có người ở chuyển vào TRƯỚC KHI tháng này kết thúc
                # Điều kiện 2: VÀ người đó chưa chuyển đi HOẶC chuyển đi SAU KHI tháng này bắt đầu
                Q(residents__move_out_date__isnull=True)
                | Q(residents__move_out_date__date__gte=start_of_bill_month),
                residents__move_in_date__date__lt=start_of_next_month,
            )
            .distinct()
            .order_by("room_id")
        )
        if search_query:
            rooms_qs = rooms_qs.filter(
                Q(room_id__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        # --- TỔNG HỢP DỮ LIỆU HÓA ĐƠN CHO TỪNG PHÒNG ---
        workspace_data = []

        # Lấy trước tất cả dữ liệu liên quan trong tháng để tối ưu hóa
        drafts_for_month = list(DraftBill.objects.filter(bill_month=month_date))
        final_bills_for_month = list(
            Bill.objects.filter(
                bill_month__year=month_date.year, bill_month__month=month_date.month
            )
        )
        today = timezone.now().date()
        start_of_current_month = today.replace(day=1)
        # Lấy cả chỉ số của tháng hiện tại và tháng trước
        current_readings_list = list(
            MonthlyMeterReading.objects.filter(service_month__date=month_date)
        )
        prev_readings_list = list(
            MonthlyMeterReading.objects.filter(service_month__date=previous_month_date)
        )
        drafts_for_month = list(DraftBill.objects.filter(bill_month=month_date))

        for room in rooms_qs:
            # tìm trong dữ liệu đã lấy
            ew_draft = next(
                (
                    d
                    for d in drafts_for_month
                    if d.room_id == room.pk and d.draft_type == "ELECTRIC_WATER"
                ),
                None,
            )
            services_draft = next(
                (
                    d
                    for d in drafts_for_month
                    if d.room_id == room.pk and d.draft_type == "SERVICES"
                ),
                None,
            )
            final_bill = next(
                (b for b in final_bills_for_month if b.room_id == room.pk), None
            )
            current_reading = next(
                (r for r in current_readings_list if r.room_id == room.pk), None
            )
            prev_reading = next(
                (r for r in prev_readings_list if r.room_id == room.pk), None
            )
            historical_residents = get_historical_residents(room, month_date)

            is_ready_to_finalize = False
            if ew_draft and services_draft:
                if (
                    ew_draft.status == "CONFIRMED"
                    and services_draft.status == "CONFIRMED"
                ):
                    is_ready_to_finalize = True

            subscribed_services_summary = []
            if (
                services_draft
                and services_draft.details
                and "services" in services_draft.details
            ):
                services_in_draft_list = services_draft.details.get("services", [])

                # Đếm số lần xuất hiện của mỗi service_id
                service_counts = Counter(
                    s["service_id"] for s in services_in_draft_list
                )

                # Lấy thông tin chi tiết của các dịch vụ đã có chỉ bằng một query
                services_info_map = {
                    s.pk: s
                    for s in AdditionalService.objects.filter(
                        pk__in=service_counts.keys()
                    )
                }

                # Tạo danh sách tóm tắt cuối cùng
                for service_id, quantity in service_counts.items():
                    service_obj = services_info_map.get(service_id)
                    if service_obj:
                        subscribed_services_summary.append(
                            {
                                "service_id": service_id,
                                "name": service_obj.name,
                                "type": service_obj.type,
                                "quantity": quantity,
                                "total_cost": float(service_obj.unit_price * quantity),
                            }
                        )

            billing_status = "NOT_STARTED"
            if final_bill:
                billing_status = "FINALIZED"
            elif ew_draft and services_draft:
                if (
                    ew_draft.status == "CONFIRMED"
                    and services_draft.status == "CONFIRMED"
                ):
                    billing_status = "READY_TO_FINALIZE"
                else:
                    billing_status = "PENDING_CONFIRMATION"
            elif ew_draft or services_draft:
                billing_status = "IN_PROGRESS"
            # Tạo dictionary "an toàn" cho JavaScript
            modal_data_for_js = {
                "room_pk": room.pk,
                "room_description": room.description,
                "is_ready_to_finalize": is_ready_to_finalize,  # <-- Thêm trạng thái sẵn sàng
                "ew_draft_pk": ew_draft.pk if ew_draft else None,
                "ew_draft_status": ew_draft.status if ew_draft else None,
                "services_draft_pk": services_draft.pk if services_draft else None,
                "services_draft_status": (
                    services_draft.status if services_draft else None
                ),
                "final_bill_pk": final_bill.pk if final_bill else None,
                "final_bill_status": final_bill.status if final_bill else None,
                "billing_status": (
                    billing_status.upper() if billing_status else "UNKNOWN"
                ),
                "prev_reading_index": (
                    float(prev_reading.electricity_index) if prev_reading else 0
                ),
                "prev_reading_water_index": (
                    float(prev_reading.water_index) if prev_reading else 0
                ),
                "current_reading_electricity": (
                    float(current_reading.electricity_index) if current_reading else ""
                ),
                "current_reading_water": (
                    float(current_reading.water_index) if current_reading else ""
                ),
                "subscribed_services": subscribed_services_summary,
            }

            # Dữ liệu đầy đủ cho template Django
            room_info = {
                "room": room,
                "residents": historical_residents,
                "ew_draft": ew_draft,
                "services_draft": services_draft,
                "final_bill": final_bill,
                "billing_status": billing_status,
                "modal_data_json": json.dumps(modal_data_for_js, cls=DjangoJSONEncoder),
            }

            # Xác định trạng thái tổng hợp của phòng trong tháng

            # room_info["billing_status"] = billing_status
            workspace_data.append(room_info)

        # Lọc lần cuối dựa trên trạng thái tổng hợp (nếu có)
        if billing_status_filter:
            workspace_data = [
                data
                for data in workspace_data
                if data["billing_status"] == billing_status_filter
            ]
        overdue_bills = Bill.objects.filter(
            status=PaymentStatus.UNPAID.value, due_date__lt=today
        ).select_related("room")

        context["overdue_bills"] = overdue_bills
        context["workspace_data"] = workspace_data
        context["addable_services"] = AdditionalService.objects.all()
        form_initial_data = {}
        if month_date:
            # Định dạng lại thành chuỗi YYYY-MM cho giá trị ban đầu của form
            form_initial_data["bill_month"] = month_date.strftime("%Y-%m")

        # Khởi tạo form với dữ liệu ban đầu và gán vào context
        context["adhoc_service_form"] = bills_form.AdhocServiceForm(
            initial=form_initial_data
        )
        return context


class RoomBillListView(RoleRequiredMixin, generic.DetailView):
    model = Room
    template_name = "manager/bills/room_bill_list.html"
    pk_url_kwarg = "room_id"
    context_object_name = "room"
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = self.get_object()
        month_raw = self.request.GET.get("month")
        month = None
        if month_raw:
            try:
                parsed_date = datetime.strptime(
                    month_raw.strip(), YEAR_MONTH_DAY_FORMAT
                ).date()
                month = parsed_date.strftime(YEAR_MONTH_DAY_FORMAT)
            except ValueError:
                month = None

        context["selected_month"] = month

        # Lấy danh sách hóa đơn cuối cùng của phòng này
        context["final_bills"] = Bill.objects.filter(room=room).order_by("-bill_month")
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

        month_raw = self.request.GET.get("month")
        month = None
        if month_raw:
            try:
                parsed_date = datetime.strptime(
                    month_raw.strip(), YEAR_MONTH_DAY_FORMAT
                ).date()
                month = parsed_date.strftime(YEAR_MONTH_DAY_FORMAT)
            except ValueError:
                month = None

        context["selected_month"] = month
        bill_month_date = bill.bill_month.date()
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


class RemoveServiceFromDraftView(RoleRequiredMixin, generic.View):
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def post(self, request, pk):
        try:
            draft_bill = get_object_or_404(DraftBill, pk=pk)
            service_id_to_remove = int(request.POST.get("service_id"))

            if not (draft_bill.details and "services" in draft_bill.details):
                return JsonResponse(
                    {"status": "error", "message": _("Không có dịch vụ nào để xóa.")},
                    status=400,
                )

            services_list = draft_bill.details.get("services", [])
            service_to_remove_found = False

            # Tìm và xóa MỘT bản ghi đầu tiên của dịch vụ được chọn
            for i, service in enumerate(services_list):
                if service.get("service_id") == service_id_to_remove:
                    services_list.pop(i)
                    service_to_remove_found = True
                    break

            if not service_to_remove_found:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": _("Không tìm thấy dịch vụ trong hóa đơn."),
                    },
                    status=404,
                )

            # Tính lại tổng tiền của toàn bộ hóa đơn nháp dịch vụ
            new_total_amount = sum(decimal.Decimal(s["cost"]) for s in services_list)
            draft_bill.total_amount = new_total_amount
            draft_bill.details["services"] = services_list
            draft_bill.save()

            # Trả về dữ liệu đã cập nhật để frontend có thể render lại
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Đã xóa dịch vụ thành công.",
                    "new_total_amount": float(new_total_amount),
                    "updated_services": services_list,
                }
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class BillDeleteView(RoleRequiredMixin, generic.DeleteView):
    model = Bill
    success_url = reverse_lazy("billing_workspace")
    pk_url_kwarg = "bill_id"
    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def get(self, request, *args, **kwargs):
        # Chặn truy cập GET, chỉ cho phép POST
        return HttpResponseNotAllowed(["POST"])

    def post(self, request, *args, **kwargs):
        bill = self.get_object()

        # Xóa các dữ liệu liên quan
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
        bill.status = "paid"
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
                timezone.datetime.strptime(month_str, YEAR_MONTH_DAY_FORMAT)
                .date()
                .replace(day=1)
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
        # trỏ về billing_workspace thay vì billing_workspace
        redirect_url = reverse("billing_workspace")
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
            month_date = timezone.datetime.strptime(
                month_str, YEAR_MONTH_DAY_FORMAT
            ).date()
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
        # Cập nhật chỉ số mới cho phòng đang được lưu
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
        ctx = super().get_context_data(**kwargs)
        bill: DraftBill = self.object
        d = bill.details or {}

        # Cờ để template biết hiển thị phần nào
        month_raw = self.request.GET.get("month")
        month = None
        if month_raw:
            try:
                clean_value = month_raw.strip().split("&")[0]
                parsed_date = datetime.strptime(
                    clean_value, YEAR_MONTH_DAY_FORMAT
                ).date()
                month = parsed_date.strftime(YEAR_MONTH_DAY_FORMAT)
            except ValueError:
                month = None

        ctx["selected_month"] = month
        ctx["is_ew"] = bill.draft_type == DraftBill.DraftType.ELECTRIC_WATER
        ctx["is_services"] = bill.draft_type == DraftBill.DraftType.SERVICES

        def fnum(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        if ctx["is_ew"]:
            rows = [
                {
                    "label": "Điện",
                    "old": d.get("old_electric_index"),
                    "new": d.get("new_electric_index"),
                    "consumption": d.get("electric_consumption"),
                    "unit_price": fnum(d.get("electric_unit_price")),
                    "amount": fnum(d.get("electric_cost")),
                },
                {
                    "label": "Nước",
                    "old": d.get("old_water_index"),
                    "new": d.get("new_water_index"),
                    "consumption": d.get("water_consumption"),
                    "unit_price": fnum(d.get("water_unit_price")),
                    "amount": fnum(d.get("water_cost")),
                },
            ]
            ctx["calc_rows"] = rows
            ctx["grand_total"] = sum(r["amount"] for r in rows)

        if ctx["is_services"]:
            # d.get("services") là list các item đã thêm vào draft
            items = d.get("services", [])
            summary = {}
            for s in items:
                sid = s.get("service_id")
                if not sid:
                    continue
                if sid not in summary:
                    unit = s.get("unit_price", s.get("cost", 0))
                    summary[sid] = {
                        "name": s.get("name", f"Dịch vụ {sid}"),
                        "type": s.get("type", ""),
                        "unit_price": fnum(unit),
                        "quantity": 0,
                        "total": 0.0,
                    }
                summary[sid]["quantity"] += 1
                summary[sid]["total"] = (
                    summary[sid]["quantity"] * summary[sid]["unit_price"]
                )

            rows = list(summary.values())
            ctx["service_rows"] = rows
            ctx["grand_total"] = sum(r["total"] for r in rows)

        # lựa chọn trạng thái cho form
        ctx["status_choices"] = DraftBill.DraftStatus.choices
        return ctx


@role_required(UserRole.APARTMENT_MANAGER.value)
@require_POST
def update_draft_bill_status_view(request, pk):
    draft_bill = get_object_or_404(DraftBill, pk=pk)
    new_status = request.POST.get("status")

    # Lấy month từ query string (nếu có)
    month = get_month_from_request(request)
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

    # Redirect, giữ nguyên month nếu có
    return redirect(
        f"{reverse('draft_bill_detail', args=[draft_bill.pk])}?month={month}"
    )


def get_month_from_request(request):
    """
    Lấy month ở dạng 'YYYY-MM-DD' từ request.POST hoặc request.GET.
    Trả về None nếu không có hoặc không hợp lệ.
    """
    month_raw = request.POST.get("month") or request.GET.get("month")
    if not month_raw:
        return None
    try:
        clean_value = month_raw.strip().split("&")[0]
        parsed_date = datetime.strptime(clean_value, YEAR_MONTH_DAY_FORMAT).date()
        return parsed_date.strftime(YEAR_MONTH_DAY_FORMAT)
    except (ValueError, AttributeError):
        return None


# tạo một hàm helper để tái sử dụng logic này
def get_historical_residents(room, bill_month):
    """
    Lấy danh sách các đối tượng RoomResident duy nhất theo user
    đã ở trong phòng tại tháng hóa đơn.
    """
    # Đảm bảo bill_month luôn là đối tượng date
    bill_month_date = (
        bill_month.date() if isinstance(bill_month, timezone.datetime) else bill_month
    )
    start_of_next_month = bill_month_date + relativedelta(months=1)

    # lấy tất cả các bản ghi RoomResident hợp lệ trong tháng (có thể bị trùng user)
    valid_resident_records = [
        res
        for res in room.residents.all()
        if res.move_in_date.date() < start_of_next_month
        and (res.move_out_date is None or res.move_out_date.date() >= bill_month_date)
    ]

    # Lọc để giữ lại duy nhất một bản ghi cho mỗi user_id
    unique_residents = []
    seen_user_ids = set()  # Dùng set để theo dõi các user_id đã gặp

    for resident_record in valid_resident_records:
        # Nếu user_id của bản ghi này chưa từng được thấy...
        if resident_record.user_id not in seen_user_ids:
            # ... thêm bản ghi này vào kết quả cuối cùng...
            unique_residents.append(resident_record)
            # ... đánh dấu là đã thấy user_id này.
            seen_user_ids.add(resident_record.user_id)

    return unique_residents


class AddAdhocServiceView(RoleRequiredMixin, generic.View):
    """
    Xử lý việc thêm thủ công một dịch vụ lẻ vào hóa đơn nháp của một phòng.
    """

    allowed_roles = UserRole.APARTMENT_MANAGER.value

    def post(self, request, *args, **kwargs):
        form = bills_form.AdhocServiceForm(request.POST)

        # Chuẩn bị URL để redirect, kể cả khi lỗi
        month_str_from_post = request.POST.get("bill_month", "")  # Format YYYY-MM
        redirect_url = request.META.get("HTTP_REFERER", reverse("billing_workspace"))
        if month_str_from_post:
            # Giữ lại tháng đã chọn trên URL khi có lỗi
            redirect_url = f"{redirect_url}?month={month_str_from_post}-01"

        if form.is_valid():
            room = form.cleaned_data["room"]
            service_to_add = form.cleaned_data["service"]
            bill_month_str = form.cleaned_data["bill_month"]

            try:
                room = Room.objects.get(pk=room)
                bill_month = timezone.datetime.strptime(bill_month_str, "%Y-%m").date()
            except (ValueError, TypeError):
                return JsonResponse(
                    {"status": "error", "message": _("Phòng hoặc tháng không hợp lệ.")},
                    status=400,
                )
                return redirect(redirect_url)

            # Tìm hoặc tạo hóa đơn nháp dịch vụ duy nhất cho phòng và tháng đó
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

            # Kiểm tra giới hạn số lượng dịch vụ
            services_in_draft = draft_bill.details.get("services", [])
            service_type = service_to_add.type.upper()
            service_counts = Counter(s["service_id"] for s in services_in_draft)

            # Lấy số người ở trong tháng để kiểm tra
            num_residents = len(get_historical_residents(room, bill_month))

            if service_type == "PER_ROOM":
                if service_to_add.pk in service_counts:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": _(
                                f"Dịch vụ '{service_to_add.name}' (theo phòng) chỉ có thể thêm một lần."
                            ),
                        },
                        status=400,
                    )

            elif service_type == "PER_PERSON":
                if num_residents == 0:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": _(
                                f"Không thể thêm dịch vụ theo người cho phòng trống."
                            ),
                        },
                        status=400,
                    )
                if service_counts.get(service_to_add.pk, 0) >= num_residents:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": _(
                                f"Đã đạt số lượng tối đa ({num_residents}) cho dịch vụ '{service_to_add.name}'."
                            ),
                        },
                        status=400,
                    )

            # 3. Tính toán chi phí cho dịch vụ mới
            cost = service_to_add.unit_price  # Mặc định là giá gốc (cho PER_ROOM)
            if service_type == "PER_PERSON":
                # Với dịch vụ theo người, chi phí của một lượt thêm luôn là đơn giá
                # Tổng tiền sẽ được tính lại dựa trên tổng số lượng
                pass

            # 4. Cập nhật hóa đơn nháp
            draft_bill.details["services"].append(
                {
                    "service_id": service_to_add.pk,
                    "name": service_to_add.name,
                    "cost": float(cost),
                    "type": service_to_add.type,
                    "unit_price": float(service_to_add.unit_price),
                }
            )

            # Tính lại tổng tiền của hóa đơn nháp dịch vụ
            new_total_amount = sum(
                decimal.Decimal(s["cost"]) for s in draft_bill.details["services"]
            )
            draft_bill.total_amount = new_total_amount
            draft_bill.save()

            # Chuẩn bị dữ liệu trả về cho frontend
            # Đây là logic tổng hợp lại danh sách dịch vụ để gửi về
            services_in_draft_list = draft_bill.details.get("services", [])
            service_counts = Counter(s["service_id"] for s in services_in_draft_list)
            services_info_map = {
                s.pk: s
                for s in AdditionalService.objects.filter(pk__in=service_counts.keys())
            }

            updated_summary = []
            for service_id, quantity in service_counts.items():
                service_obj = services_info_map.get(service_id)
                if service_obj:
                    updated_summary.append(
                        {
                            "service_id": service_id,
                            "name": service_obj.name,
                            "type": service_obj.type,
                            "quantity": quantity,
                            "total_cost": float(service_obj.unit_price * quantity),
                        }
                    )

            return JsonResponse(
                {
                    "status": "success",
                    "message": _(f"Đã thêm dịch vụ '{service_to_add.name}'."),
                    "updated_services_summary": updated_summary,  # Gửi lại danh sách đã cập nhật
                    "services_draft_pk": draft_bill.pk,
                }
            )
        else:
            return JsonResponse(
                {
                    "status": "error",
                    "message": _("Dữ liệu không hợp lệ."),
                    "errors": form.errors,
                },
                status=400,
            )


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

        month_date = timezone.datetime.strptime(month_str, YEAR_MONTH_DAY_FORMAT).date()
        room = get_object_or_404(Room, pk=room_id)
        redirect_url = f"{reverse('billing_workspace')}?month={month_str}"

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


@role_required(UserRole.APARTMENT_MANAGER.value)
@require_POST
def send_payment_reminders_view(request):
    bill_ids = request.POST.getlist("bill_ids")

    if not bill_ids:
        messages.warning(
            request, _("Vui lòng chọn ít nhất một hóa đơn để gửi nhắc nhở.")
        )
        return redirect("billing_workspace")

    today = timezone.now().date()

    # Truy vấn trực tiếp đến database để lấy tất cả các hóa đơn
    # thỏa mãn 2 điều kiện:
    # 1. Trạng thái là 'chưa thanh toán'
    # 2. VÀ ngày hết hạn (due_date) nhỏ hơn ngày hôm nay
    overdue_bills = Bill.objects.filter(
        status=PaymentStatus.UNPAID.value, due_date__lt=today
    ).select_related("room")

    notifications_created_count = 0
    for bill in overdue_bills:
        # Tìm tất cả cư dân trong phòng của hóa đơn đó
        residents = RoomResident.objects.filter(room=bill.room)
        for resident in residents:
            title = (
                f"Nhắc nhở thanh toán hóa đơn tháng {bill.bill_month.strftime('%m/%Y')}"
            )
            message = (
                f"Chào {resident.user.full_name},\n\n"
                f"Hệ thống ghi nhận hóa đơn #{bill.bill_id} cho phòng {bill.room.description} "
                f"với tổng số tiền {bill.total_amount:,.0f} VNĐ đã quá hạn thanh toán.\n\n"
                f"Vui lòng thanh toán sớm. Cảm ơn bạn."
            )

            # Tạo thông báo từ Manager gửi đến Cư dân
            Notification.objects.create(
                sender=request.user,
                receiver=resident.user,
                title=title,
                message=message,
            )
            notifications_created_count += 1

    if notifications_created_count > 0:
        messages.success(
            request,
            _(f"Đã gửi thành công {notifications_created_count} thông báo nhắc nhở."),
        )
    else:
        messages.warning(
            request, _("Không có hóa đơn hợp lệ nào được chọn để gửi thông báo.")
        )

    # Chuyển hướng lại trang workspace với tháng đã chọn (nếu có)
    month_str = request.POST.get("month_param", "")
    redirect_url = reverse("billing_workspace")
    if month_str:
        redirect_url = f"{redirect_url}?month={month_str}"

    return redirect(redirect_url)
