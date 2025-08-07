from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator

from appartment.constants import UserRole
from appartment.utils.permissions import role_required
from ...models import Province, District, Ward, User
from ...forms.admin.user_form import UserCreateForm, UserUpdateForm
from ...constants import PaginateNumber


@login_required
@role_required(UserRole.ADMIN.value)
def create_user(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # If exist province return object else create new object
            province = Province.objects.get_or_create(
                province_name=data["province_name"], province_code=data["province_code"]
            )[0]

            # #If exist district return object else create new object
            district = District.objects.get_or_create(
                district_name=data["district_name"],
                district_code=data["district_code"],
                province=province,
            )[0]

            # If exist ward return object else create new object
            ward = Ward.objects.get_or_create(
                ward_name=data["ward_name"],
                ward_code=data["ward_code"],
                district=district,
            )[0]

            # Set default password = user_id + phone
            raw_password = f"{data['user_id']}{data['phone']}"

            # Create user
            User.objects.create_user(
                email=data["email"],
                password=raw_password,
                user_id=data["user_id"],
                full_name=data["full_name"],
                phone=data["phone"],
                role=data["role"],
                province=province,
                district=district,
                ward=ward,
                detail_address=data["detail_address"],
                is_active=(data["status"] == "True"),
            )

            messages.success(
                request,
                _("Thêm người dùng thành công! Mật khẩu mặc định: %(password)s")
                % {"password": raw_password},
            )
            return redirect("user_list")
    else:
        form = UserCreateForm()

    return render(request, "admin/user_create.html", {"form": form})


@login_required
@role_required(UserRole.ADMIN.value)
def user_list(request):
    q = request.GET.get("q", "")  # searched word

    users = User.objects.select_related("role").order_by("-created_at")

    if q:
        users = users.filter(
            Q(full_name__icontains=q)
            | Q(email__icontains=q)
            | Q(phone__icontains=q)
            | Q(role__role_name__icontains=q)
        )

    paginator = Paginator(users, PaginateNumber.P_SHORT.value)
    page_number = request.GET.get("page")
    users_page = paginator.get_page(page_number)

    return render(
        request,
        "admin/user_list.html",
        {"users": users_page, "q": q},
    )


@login_required
@role_required(UserRole.ADMIN.value)
def update_user(request, user_id):
    try:
        user = User.objects.select_related("province", "district", "ward").get(
            user_id=user_id
        )
    except User.DoesNotExist:
        messages.error(
            request, _("Người dùng với ID %(id)s không tồn tại.") % {"id": user_id}
        )
        return redirect("user_list")

    if request.method == "POST":
        # Update form
        form = UserUpdateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Update province
            province = Province.objects.get_or_create(
                province_name=data["province_name"], province_code=data["province_code"]
            )[0]

            # Update district
            district = District.objects.get_or_create(
                district_name=data["district_name"],
                district_code=data["district_code"],
                province=province,
            )[0]

            # Update ward
            ward = Ward.objects.get_or_create(
                ward_name=data["ward_name"],
                ward_code=data["ward_code"],
                district=district,
            )[0]

            # Update user
            user.full_name = data["full_name"]
            user.email = data["email"]
            user.phone = data["phone"]
            user.detail_address = data["detail_address"]
            user.role = data["role"]
            user.province = province
            user.district = district
            user.ward = ward
            user.is_active = data["status"] == "True"
            user.save()

            messages.success(
                request,
                _("Cập nhật người dùng %(full_name)s dùng thành công!")
                % {"full_name": user.full_name},
            )
            return redirect("user_list")

    else:
        # Show form
        form = UserUpdateForm(
            initial={
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "detail_address": user.detail_address,
                "role": user.role,
                "status": str(user.is_active),
                "province_name": user.province.province_name if user.province else "",
                "province_code": user.province.province_code if user.province else "",
                "district_name": user.district.district_name if user.district else "",
                "district_code": user.district.district_code if user.district else "",
                "ward_name": user.ward.ward_name if user.ward else "",
                "ward_code": user.ward.ward_code if user.ward else "",
            }
        )

    return render(request, "admin/user_update.html", {"form": form})


@login_required
@role_required(UserRole.ADMIN.value)
def delete_user(request, user_id):
    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        messages.error(
            request,
            _("Người dùng ID %(user_id)s không tồn tại.") % {"user_id": user_id},
        )
        return redirect("user_list")

    if request.method == "POST":
        user.delete()
        messages.success(
            request,
            _("Đã xóa người dùng %(full_name)s thành công.")
            % {"full_name": user.full_name},
        )
        return redirect("user_list")

    messages.error(request, _("Yêu cầu không hợp lệ."))
    return redirect("user_list")


@login_required
@role_required(UserRole.ADMIN.value)
def toggle_active(request, user_id):
    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        messages.error(
            request,
            _("Người dùng ID %(user_id)s không tồn tại.") % {"user_id": user_id},
        )
        return redirect("user_list")

    if request.method == "POST":
        user.is_active = not user.is_active
        user.save()

    return redirect("user_list")
