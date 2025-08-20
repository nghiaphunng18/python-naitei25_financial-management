# utils/permissions.py
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views import generic
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
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


class RoleRequiredMixin(AccessMixin):
    """
    Mixin cho Class-Based View để kiểm tra quyền truy cập dựa trên vai trò của người dùng.
    """

    # --- Các thuộc tính có thể tùy chỉnh trong View của bạn ---

    # Danh sách các vai trò được phép truy cập. BẮT BUỘC phải được định nghĩa trong View.
    allowed_roles = None

    # URL để chuyển hướng nếu người dùng không có quyền.
    permission_denied_redirect = "dashboard"

    # Thông báo lỗi sẽ hiển thị.
    permission_denied_message = _("Bạn không có quyền truy cập chức năng này.")

    def get_allowed_roles(self):
        """
        Trả về thuộc tính allowed_roles.
        Báo lỗi nếu nó không được định nghĩa trong View.
        """
        if self.allowed_roles is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the 'allowed_roles' attribute. "
                "Define 'allowed_roles' in your view or override 'get_allowed_roles()'."
            )
        return self.allowed_roles

    def has_required_role(self):
        """
        Kiểm tra xem người dùng hiện tại có vai trò nằm trong danh sách được phép không.
        """
        user = self.request.user
        user_role = getattr(user.role, "role_name", None)
        return user_role in self.get_allowed_roles()

    def dispatch(self, request, *args, **kwargs):
        """
        Ghi đè phương thức dispatch để thực hiện kiểm tra quyền trước khi View được thực thi.
        """
        # 1. Kiểm tra người dùng đã đăng nhập chưa.
        #    Nếu chưa, AccessMixin sẽ tự động xử lý và chuyển hướng đến trang login.
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # 2. Nếu đã đăng nhập, kiểm tra vai trò (role).
        if not self.has_required_role():
            messages.error(request, self.permission_denied_message)
            return redirect(self.permission_denied_redirect)

        # 3. Nếu tất cả đều hợp lệ, tiếp tục xử lý request.
        return super().dispatch(request, *args, **kwargs)
