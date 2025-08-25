from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.db.models import Max

from appartment.constants import UserRole
from appartment.utils.permissions import role_required
from ...models import Province, District, Ward, User
from ...forms.admin.user_form import UserCreateForm, UserUpdateForm
from ...constants import PaginateNumber, StringLength


def generate_user_id():
    max_length = StringLength.SHORT.value

    all_ids = User.objects.values_list("user_id", flat=True)
    numeric_ids = []

    for uid in all_ids:
        try:
            numeric_ids.append(int(uid))
        except (ValueError, TypeError):
            continue

    last_num = max(numeric_ids) if numeric_ids else 0
    new_num = last_num + 1
    new_id = str(new_num)

    if len(new_id) > max_length:
        raise ValueError(_("Không thể sinh thêm user_id vì đã đạt giới hạn độ dài."))

    return new_id


@login_required
@role_required(UserRole.ADMIN.value)
def create_user(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

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
                province=data["province"],
                district=data["district"],
                ward=data["ward"],
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
        new_user_id = generate_user_id()
        form = UserCreateForm(initial={"user_id": new_user_id})

    return render(
        request,
        "admin/partials/user_create.html",{"form": form,},
    )


@login_required
@role_required(UserRole.ADMIN.value)
def user_list(request):
    q = request.GET.get("q", "")
    qs = (
        User.objects.select_related("role")
        .filter(is_deleted=False)
        .order_by("-created_at", "-pk")
    )
    if q:
        qs = qs.filter(
            Q(full_name__icontains=q)
            | Q(email__icontains=q)
            | Q(phone__icontains=q)
            | Q(role__role_name__icontains=q)
        )
    paginator = Paginator(qs, PaginateNumber.P_SHORT.value)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "admin/user_list.html",
        {"users": page_obj, "q": q},
    )


@login_required
@role_required(UserRole.ADMIN.value)
def update_user(request, user_id):
    try:
        user = User.objects.get(user_id=user_id)
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

            # Update user
            user.full_name = data["full_name"]
            user.email = data["email"]
            user.phone = data["phone"]
            user.detail_address = data["detail_address"]
            user.role = data["role"]
            user.province = data["province"]
            user.district = data["district"]
            user.ward = data["ward"]
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
                "province": user.province,
                "district": user.district,
                "ward": user.ward,
            }
        )

    return render(
        request,
        "admin/partials/user_update.html",
        {"form": form, "user_id": user.user_id},
    )


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
        user.is_deleted = True
        user.is_active = False
        user.save(update_fields=["is_deleted", "is_active"])

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
        if user.is_active:
            messages.success(
                request,
                _("Kích hoạt tài khoản %(full_name)s thành công.")
                % {"full_name": user.full_name},
            )
        else:
            messages.success(
                request,
                _("Vô hiệu hóa tài khoản %(full_name)s thành công.")
                % {"full_name": user.full_name},
            )
    return redirect("user_list")


@login_required
@role_required(UserRole.ADMIN.value)
def load_districts(request):
    province_id = request.GET.get("province")
    districts = District.objects.filter(province_id=province_id).order_by(
        "district_name"
    )
    return render(
        request,
        "admin/partials/district_options.html",
        {"districts": districts},
    )


@login_required
@role_required(UserRole.ADMIN.value)
def load_wards(request):
    district_id = request.GET.get("district")
    wards = Ward.objects.filter(district_id=district_id).order_by("ward_name")
    return render(
        request,
        "admin/partials/ward_options.html",
        {"wards": wards},
    )
