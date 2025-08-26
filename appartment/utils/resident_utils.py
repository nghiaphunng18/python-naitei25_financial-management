from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.translation import gettext as _

from ..constants import DEFAULT_PAGE_SIZE
from ..models import RoomResident


def _filter_by_status(residents, filter_status):
    if filter_status != "all":
        if filter_status == "no_room":
            residents = residents.filter(
                Q(roomresident__isnull=True)
                | ~Q(roomresident__move_out_date__isnull=True)
            ).distinct()
        elif filter_status == "in_room":
            residents = residents.filter(
                roomresident__move_out_date__isnull=True
            ).distinct()
        elif filter_status == "left_room":
            residents = residents.filter(
                roomresident__isnull=False, roomresident__move_out_date__isnull=False
            ).distinct()
    return residents


def _filter_by_active(residents, filter_active):
    if filter_active != "all":
        is_active = filter_active == "active"
        residents = residents.filter(is_active=is_active)
    return residents


def _search_residents(residents, search_query):
    if search_query:
        residents = residents.filter(
            Q(full_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(phone__icontains=search_query)
        )
    return residents


def _sort_residents(residents, sort_by):
    if sort_by == "name_asc":
        residents = residents.order_by("full_name")
    elif sort_by == "name_desc":
        residents = residents.order_by("-full_name")
    elif sort_by == "email_asc":
        residents = residents.order_by("email")
    elif sort_by == "email_desc":
        residents = residents.order_by("-email")
    return residents


def filter_residents(request, base_query):
    # Lấy các tham số từ GET
    filter_status = request.GET.get("filter_status", "all")
    filter_active = request.GET.get("filter_active", "all")
    search_query = request.GET.get("search_query", "")
    sort_by = request.GET.get("sort_by", "name_asc")

    residents = base_query.select_related("province", "district", "ward")

    # Lọc theo trạng thái phòng
    residents = _filter_by_status(residents, filter_status)

    # Lọc theo trạng thái hoạt động
    residents = _filter_by_active(residents, filter_active)

    # Tìm kiếm
    residents = _search_residents(residents, search_query)

    # Sắp xếp
    residents = _sort_residents(residents, sort_by)

    # Phân trang
    paginator = Paginator(residents, DEFAULT_PAGE_SIZE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Tạo danh sách resident_data
    resident_data = []
    for resident in page_obj:
        address_parts = []
        if resident.detail_address:
            address_parts.append(resident.detail_address)
        if resident.ward:
            address_parts.append(resident.ward.ward_name)
        if resident.district:
            address_parts.append(resident.district.district_name)
        if resident.province:
            address_parts.append(resident.province.province_name)
        address = ", ".join(address_parts) if address_parts else _("Chưa có địa chỉ")

        # Get the current room
        current_room = (
            RoomResident.objects.filter(user=resident, move_out_date__isnull=True)
            .select_related("room")
            .first()
        )
        room_id = current_room.room.room_id if current_room else _("Chưa có phòng")

        resident_data.append(
            {
                "user_id": resident.user_id,
                "full_name": resident.full_name,
                "email": resident.email,
                "phone": resident.phone,
                "address": address,
                "room_id": room_id,
                "is_active": resident.is_active,
                "history": RoomResident.objects.filter(user=resident).select_related(
                    "room"
                ),
            }
        )

    context = {
        "residents": page_obj,
        "resident_data": resident_data,
        "filter_status": filter_status,
        "filter_active": filter_active,
        "search_query": search_query,
        "sort_by": sort_by,
    }

    # Tạo query_params cho phân trang
    query_params = []
    if filter_status:
        query_params.append(f"filter_status={filter_status}")
    if filter_active:
        query_params.append(f"filter_active={filter_active}")
    if search_query:
        query_params.append(f"search_query={search_query}")
    if sort_by:
        query_params.append(f"sort_by={sort_by}")
    query_params = "&".join(query_params)
    context["query_params"] = query_params

    return context
