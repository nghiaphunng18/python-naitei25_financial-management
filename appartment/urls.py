from django.urls import include
from django.urls import path
from appartment.views import auth_views, base_views, dashboard_views
from appartment.views import auth_views, base_views
from appartment.views import auth_views
from appartment.views.manager import room_views


urlpatterns = [
    path("", base_views.index, name="index"),
    path("login/", auth_views.login_view, name="login"),
    path("logout/", auth_views.logout_view, name="logout"),
    path("dashboard", dashboard_views.dashboard, name="dashboard"),
    path("create_room", room_views.create_room, name="create_room"),
    path("room_list", room_views.room_list, name="room_list"),
    path("<str:room_id>/", room_views.room_detail, name="room_detail"),
    path("<str:room_id>/edit/", room_views.room_update, name="room_update"),
]
