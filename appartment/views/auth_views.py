from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
from ..forms.auth_forms import LoginForm


@csrf_protect
def login_view(request):
    """
    View xử lý đăng nhập người dùng
    """
    # Nếu người dùng đã đăng nhập thì chuyển hướng về trang chính
    # if request.user.is_authenticated:
    #     return redirect("/")  # hoặc trang chính
    if request.method == "GET" and "next" in request.GET:
        messages.warning(request, _("Bạn cần đăng nhập để truy cập trang này."))

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            # Xác thực người dùng
            user = authenticate(request, username=email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(
                        request,
                        _("Chào mừng %(name)s!") % {"name": user.get_full_name()},
                    )
                    # Chuyển hướng đến trang ban đầu hoặc dashboard
                    next_url = request.GET.get("next", "dashboard")
                    return redirect(next_url)
                else:
                    messages.error(request, _("Tài khoản của bạn đã bị vô hiệu hóa."))
            else:
                messages.error(request, _("Email hoặc mật khẩu không chính xác."))
    else:
        form = LoginForm()

    return render(request, "auth/login.html", {"form": form})


@require_POST
@login_required
def logout_view(request):
    """
    View xử lý đăng xuất người dùng
    """
    logout(request)
    messages.success(request, _("Bạn đã đăng xuất thành công."))
    return redirect("index")
