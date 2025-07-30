from django.urls import include
from django.urls import path
from appartment.views import auth_views

urlpatterns = [
    path("login/", auth_views.login_view, name="login"),
    path("logout/", auth_views.logout_view, name="logout"),
]
