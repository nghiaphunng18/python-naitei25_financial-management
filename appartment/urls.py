from django.urls import include
from django.urls import path
from appartment.views import auth_views, base_views, dashboard_views

urlpatterns = [
    path("", base_views.index, name="index"),
    path("login/", auth_views.login_view, name="login"),
    path("logout/", auth_views.logout_view, name="logout"),
    path("dashboard", dashboard_views.dashboard, name="dashboard"),
]
