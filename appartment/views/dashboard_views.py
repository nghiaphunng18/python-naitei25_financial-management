from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.contrib import messages

from appartment.constants import UserRole
from .admin.dashboard_view import admin_dashboard
from .resident.dashboard_view import resident_dashboard
from .manager.manager_dashboard_views import manager_dashboard

from .admin.dashboard_view import admin_dashboard
from .manager.manager_dashboard_views import manager_dashboard


@login_required
def dashboard(request):
    user = request.user
    role = user.role.role_name
    context = {"user": user}

    if role == UserRole.ADMIN.value:
        return admin_dashboard(request, context)
    elif role == UserRole.APARTMENT_MANAGER.value:
        return manager_dashboard(request, context)
    elif role == UserRole.RESIDENT.value:
        return resident_dashboard(request, context)
    else:
        messages.error(request, _("Bạn không có quyền truy cập trang dashboard này."))
        return redirect("index")
