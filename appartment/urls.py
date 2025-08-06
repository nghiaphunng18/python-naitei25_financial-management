from django.urls import path
from appartment.views.auth_views import login_view, logout_view
from appartment.views.base_views import index
from appartment.views.dashboard_views import dashboard
from appartment.views.manager.resident_views import (
    resident_list,
    assign_room,
    leave_room,
)
from appartment.views.manager import room_views, room_history_views, bills_view
from appartment.views import auth_views, base_views, dashboard_views

urlpatterns = [
    path("", index, name="index"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard", dashboard, name="dashboard"),
    path("create_room", room_views.create_room, name="create_room"),
    path("room_list", room_views.room_list, name="room_list"),
    path("residents/", resident_list, name="resident_list"),
    path("resident/assign/<str:user_id>/", assign_room, name="assign_room"),
    path("resident/leave/<str:user_id>/", leave_room, name="leave_room"),
    path("<str:room_id>/", room_views.room_detail, name="room_detail"),
    path("<str:room_id>/edit/", room_views.room_update, name="room_update"),
    path(
        "<str:room_id>/history/",
        room_history_views.get_room_history,
        name="room_history",
    ),
    path("bills_list", bills_view.bills_list_view.as_view(), name="bills_list"),
    path("bill/create/", bills_view.BillCreateView.as_view(), name="bill_create"),
    path("bill/<str:bill_id>/", bills_view.BillDetailView.as_view(), name="bill"),
    path(
        "bill/<str:bill_id>/update/",
        bills_view.BillUpdateView.as_view(),
        name="bill_update",
    ),
    path(
        "bill/<str:bill_id>/delete/",
        bills_view.BillDeleteView.as_view(),
        name="bill_delete",
    ),
    path(
        "bill/<str:bill_id>/confirm_payment/",
        bills_view.confirm_payment_view,
        name="bill_confirm_payment",
    ),
    path(
        "bill/<str:bill_id>/print/",
        bills_view.BillPrintView.as_view(),
        name="bill_print",
    ),
]
