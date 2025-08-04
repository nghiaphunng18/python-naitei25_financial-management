from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.contrib import messages


@login_required
def dashboard(request):
    user = request.user
    role = user.role.role_name
    context = {"user": user}

    if role == "ROLE_ADMIN":
        template_name = "admin/dashboard.html"
        return render(request, template_name, context)
    elif role == "ROLE_APARTMENT_MANAGER":
        template_name = "manager/dashboard.html"
        return render(request, template_name, context)
    elif role == "ROLE_RESIDENT":
        template_name = "resident/dashboard.html"
        return render(request, template_name, context)
    else:
        messages.error(request, _("Bạn không có quyền truy cập trang dashboard này."))
        return redirect("index")
