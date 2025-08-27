from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..forms.profile import UserProfileForm


@login_required
def profile_view(request):
    """
    View để hiển thị thông tin profile của user đang đăng nhập
    Tự động chọn template phù hợp dựa trên role
    """
    user = request.user

    # Lấy thông tin địa chỉ đầy đủ
    address_parts = []
    if user.detail_address:
        address_parts.append(user.detail_address)
    if user.ward:
        address_parts.append(user.ward.ward_name)
    if user.district:
        address_parts.append(user.district.district_name)
    if user.province:
        address_parts.append(user.province.province_name)

    full_address = (
        ", ".join(address_parts) if address_parts else "Chưa cập nhật"
    )

    # Get role name and colors based on role
    role_name = user.role.role_name if user.role else "Chưa xác định"
    colors = get_role_colors(role_name)

    context = {
        "user": user,
        "full_address": full_address,
        "role_name": role_name,
        "colors": colors,
        "is_edit_mode": False,
    }

    # Chọn template dựa trên role
    role_name_lower = role_name.lower() if role_name else "role_resident"

    template_mapping = {
        "role_resident": "profile/resident_profile.html",
        "role_apartment_manager": "profile/manager_profile.html",
        "role_admin": "profile/admin_profile.html",
    }

    template_name = template_mapping.get(
        role_name_lower, "profile/resident_profile.html"
    )

    return render(request, template_name, context)


@login_required
def profile_edit_view(request):
    """
    View để hiển thị và xử lý form chỉnh sửa thông tin profile
    Tự động chọn template phù hợp dựa trên role
    """
    user = request.user

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=user)

        if form.is_valid():
            # Check if anything actually changed
            if form.has_changed():
                form.save()
                messages.success(
                    request, "Thông tin cá nhân đã được cập nhật thành công!"
                )
            else:
                messages.info(request, "Không có thông tin nào được thay đổi.")

            return redirect("profile")
        else:
            # If form is invalid, show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = UserProfileForm(instance=user)

    # Lấy thông tin địa chỉ đầy đủ (same as profile_view)
    address_parts = []
    if user.detail_address:
        address_parts.append(user.detail_address)
    if user.ward:
        address_parts.append(user.ward.ward_name)
    if user.district:
        address_parts.append(user.district.district_name)
    if user.province:
        address_parts.append(user.province.province_name)

    full_address = (
        ", ".join(address_parts) if address_parts else "Chưa cập nhật"
    )

    # Get role name and colors
    role_name = user.role.role_name if user.role else "Chưa xác định"
    colors = get_role_colors(role_name)

    context = {
        "user": user,
        "form": form,
        "full_address": full_address,
        "role_name": role_name,
        "colors": colors,
        "is_edit_mode": True,
    }

    # Chọn template dựa trên role (same mapping as profile_view)
    role_name_lower = role_name.lower() if role_name else "role_resident"

    template_mapping = {
        "role_resident": "profile/resident_profile.html",
        "role_apartment_manager": "profile/manager_profile.html",
        "role_admin": "profile/admin_profile.html",
    }

    template_name = template_mapping.get(
        role_name_lower, "profile/resident_profile.html"
    )

    return render(request, template_name, context)


def get_role_colors(role_name):
    """Get color classes based on user role"""
    role_lower = role_name.lower()

    if "resident" in role_lower:
        return {
            "gradient": "from-blue-500 to-blue-600",
            "badge": "bg-blue-100 text-blue-800",
            "focus_ring": "focus:ring-blue-500",
            "info_bg": "bg-blue-50",
            "info_icon": "text-blue-400",
            "info_text": "text-blue-800",
            "info_content": "text-blue-700",
        }
    elif "manager" in role_lower:
        return {
            "gradient": "from-green-500 to-green-600",
            "badge": "bg-green-100 text-green-800",
            "focus_ring": "focus:ring-green-500",
            "info_bg": "bg-green-50",
            "info_icon": "text-green-400",
            "info_text": "text-green-800",
            "info_content": "text-green-700",
        }
    else:  # admin or other roles
        return {
            "gradient": "from-purple-500 to-purple-600",
            "badge": "bg-purple-100 text-purple-800",
            "focus_ring": "focus:ring-purple-500",
            "info_bg": "bg-purple-50",
            "info_icon": "text-purple-400",
            "info_text": "text-purple-800",
            "info_content": "text-purple-700",
        }
