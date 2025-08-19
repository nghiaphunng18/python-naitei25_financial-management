from django.urls import path
from appartment.views.admin import admin_user_view
from appartment.views.auth_views import login_view, logout_view
from appartment.views.base_views import index
from appartment.views.dashboard_views import dashboard
from appartment.views.manager.resident_views import (
    resident_list,
    assign_room,
    leave_room,
)
from appartment.views.manager import room_views, room_history_views, bills_view
from appartment.views.resident import bill_history_views, resident_room_views
from appartment.views import auth_views, base_views, dashboard_views
from appartment.views.notification_history import (
    admin_notification_history,
    manager_notification_history,
    resident_notification_history,
    mark_notification_read,
)

urlpatterns = [
    path("", index, name="index"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard", dashboard, name="dashboard"),
    path(
        "my-bill",
        bill_history_views.resident_bill_history,
        name="bill_history",
    ),
    path("create_room", room_views.create_room, name="create_room"),
    path("room_list", room_views.room_list, name="room_list"),
    # manager: manage resident
    path("residents/", resident_list, name="resident_list"),
    path("resident/assign/<str:user_id>/", assign_room, name="assign_room"),
    path("resident/leave/<str:user_id>/", leave_room, name="leave_room"),
    # notification for all role
    path(
        "resident/notifications/",
        resident_notification_history,
        name="resident_notification_history",
    ),
    path(
        "manager/notifications/",
        manager_notification_history,
        name="manager_notification_history",
    ),
    path(
        "admin/notifications/",
        admin_notification_history,
        name="admin_notification_history",
    ),
    path(
        "notifications/mark-read/<int:notification_id>/",
        mark_notification_read,
        name="mark_notification_read",
    ),
    # room
    path("<str:room_id>/", room_views.room_detail, name="room_detail"),
    path("<str:room_id>/edit/", room_views.room_update, name="room_update"),
    path(
        "<str:room_id>/history/",
        room_history_views.get_room_history,
        name="room_history",
    ),
    # bill
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
    path(
        "resident_room_list", resident_room_views.room_list, name="resident_room_list"
    ),
    path(
        "resident/<str:room_id>",
        resident_room_views.room_detail,
        name="resident_room_detail",
    ),
    path(
        "resident/<str:room_id>/history",
        resident_room_views.room_history,
        name="resident_room_history",
    ),
    # ADMIN URL
    path("admin/user/create/", admin_user_view.create_user, name="create_user"),
    path(
        "admin/user/update/<str:user_id>",
        admin_user_view.update_user,
        name="update_user",
    ),
    path("user_list", admin_user_view.user_list, name="user_list"),
    path(
        "user/toggle-active/<str:user_id>/",
        admin_user_view.toggle_active,
        name="toggle_active",
    ),
    path("user/<str:user_id>/delete/", admin_user_view.delete_user, name="delete_user"),
]
