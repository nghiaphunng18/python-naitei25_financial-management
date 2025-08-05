# utils/permissions.py
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _


def staff_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(
                request, _("Bạn không có quyền truy cập chức năng này.")
            )
            return redirect("appartment")  # hoặc trang khác phù hợp
        return view_func(request, *args, **kwargs)

    return _wrapped_view
