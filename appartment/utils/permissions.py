# utils/permissions.py
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views import generic
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from datetime import datetime


def staff_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, _("Bạn không có quyền truy cập chức năng này."))
            return redirect("appartment")  # hoặc trang khác phù hợp
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def role_required(*allowed_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                messages.error(
                    request, _("Bạn cần đăng nhập để truy cập chức năng này.")
                )
                return redirect("login")

            user_role = getattr(user.role, "role_name", None)
            if user_role not in allowed_roles:
                messages.error(request, _("Bạn không có quyền truy cập chức năng này."))
                return redirect("dashboard")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


class StaffRequiredMixin(AccessMixin):
    """
    Mixin này kiểm tra xem người dùng hiện tại có phải là nhân viên (is_staff=True) hay không.
    Nếu không, sẽ trả về lỗi 403 Forbidden.
    """

    def dispatch(self, request, *args, **kwargs):
        # Kiểm tra xem người dùng đã đăng nhập chưa
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Kiểm tra xem người dùng có phải là nhân viên không (dựa trên is_staff)
        if not request.user.is_staff:
            raise PermissionDenied("Bạn không có quyền truy cập trang này.")

        # Nếu tất cả kiểm tra đều qua, tiếp tục xử lý request
        return super().dispatch(request, *args, **kwargs)
