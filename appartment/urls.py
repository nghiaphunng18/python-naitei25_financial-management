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
from appartment.views.manager import (
    room_views,
    room_history_views,
    bills_view,
    rental_prices_views,
)
from appartment.views.resident import (
    bill_history_views,
    resident_room_views,
    bank_payment_views,
)
from appartment.views.notification_history import (
    admin_notification_history,
    manager_notification_history,
    resident_notification_history,
    mark_notification_read,
)
from appartment.views.notification_send import (
    admin_send_notification,
    manager_send_notification,
    resident_send_notification,
    load_users_by_role,
)
from .views.profile_views import profile_view, profile_edit_view

urlpatterns = [
    # === CÁC URL TĨNH, CỤ THỂ NHẤT (ƯU TIÊN CAO NHẤT) ===
    path("", index, name="index"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    # notification
    path(
        "notification/load-users/",
        load_users_by_role,
        name="load_users_by_role",
    ),
    # MANAGER URL
    path(
        "manager/send-notification/",
        manager_send_notification,
        name="manager_send_notification",
    ),
    # MANAGER bill
    path("profile/", profile_view, name="profile"),
    path("profile/edit", profile_edit_view, name="profile_edit"),
    path(
        "manager/billing/workspace/",
        bills_view.BillingWorkspaceView.as_view(),
        name="billing_workspace",
    ),
    path(
        "manager/bill/utility_totals",
        bills_view.BuildingUtilityTotalView.as_view(),
        name="utility_totals",
    ),
    path(
        "manager/bill/generate-final-bill/",
        bills_view.GenerateFinalBillView.as_view(),
        name="generate_final_bill",
    ),
    path(
        "manager/bill/add-adhoc-service/",
        bills_view.AddAdhocServiceView.as_view(),
        name="add_adhoc_service",
    ),
    path(
        "manager/bill/<str:bill_id>/",
        bills_view.BillDetailView.as_view(),
        name="bill",
    ),
    # path("bill/<str:bill_id>/update/", bills_view.BillUpdateView.as_view(), name="bill_update"),
    path(
        "manager/bill/<str:bill_id>/delete/",
        bills_view.BillDeleteView.as_view(),
        name="bill_delete",
    ),
    path(
        "manager/bill/<str:bill_id>/confirm_payment/",
        bills_view.confirm_payment_view,
        name="bill_confirm_payment",
    ),
    path(
        "manager/bill/<str:bill_id>/print/",
        bills_view.BillPrintView.as_view(),
        name="bill_print",
    ),
    path(
        "manager/bill/draft-bill/<int:pk>/",
        bills_view.DraftBillDetailView.as_view(),
        name="draft_bill_detail",
    ),
    path(
        "manager/bill/draft-bill/<int:pk>/remove-service/",
        bills_view.RemoveServiceFromDraftView.as_view(),
        name="remove_service_from_draft",
    ),
    path(
        "manager/bill/draft-bill/<int:pk>/update-status/",
        bills_view.update_draft_bill_status_view,
        name="update_draft_bill_status",
    ),
    path(
        "manager/bill/room/<str:room_id>/save-reading/",
        bills_view.SaveMeterReadingView.as_view(),
        name="save_meter_reading",
    ),
    # MANAGER room
    path("manager/room_list", room_views.room_list, name="room_list"),
    path("manager/<str:room_id>/", room_views.room_detail, name="room_detail"),
    path("manager/create_room", room_views.create_room, name="create_room"),
    path(
        "manager/<str:room_id>/edit/",
        room_views.room_update,
        name="room_update",
    ),
    path(
        "room/<str:room_id>/bills/",
        bills_view.RoomBillListView.as_view(),
        name="room_bill_list",
    ),
    path(
        "manager/<str:room_id>/history/",
        room_history_views.get_room_history,
        name="room_history",
    ),
    path(
        "manager/rental_prices/create/<str:room_id>/",
        rental_prices_views.rental_price_create,
        name="rental_price_create",
    ),
    path(
        "manager/rental_prices/update/<int:rental_price_id>/",
        rental_prices_views.rental_price_update,
        name="rental_price_update",
    ),
    path(
        "manager/rental_prices/delete/<int:rental_price_id>/",
        rental_prices_views.rental_price_delete,
        name="rental_price_delete",
    ),
    # MANAGER manage resident
    path("manager/resident_list", resident_list, name="resident_list"),
    path("manager/assign/<str:user_id>/", assign_room, name="assign_room"),
    path("manager/leave/<str:user_id>/", leave_room, name="leave_room"),
    # MANAGER notification
    path(
        "manager/notification",
        manager_notification_history,
        name="manager_notification_history",
    ),
    # RESIDENT URL
    path(
        "resident/send-notification/",
        resident_send_notification,
        name="resident_send_notification",
    ),
    # RESIDENT bill
    path(
        "resident/my-bill",
        bill_history_views.resident_bill_history,
        name="bill_history",
    ),
    path(
        "resident/bank_payment/create/<str:bill_id>/",
        bank_payment_views.create_payment,
        name="create_payment",
    ),
    path(
        "resident/bank_payment/webhook/",
        bank_payment_views.payos_webhook,
        name="payos_webhook",
    ),
    path(
        "resident/bank_payment/transact_success/",
        bank_payment_views.payment_success,
        name="payment_success",
    ),
    path(
        "resident/bank_payment/transact_cancel/",
        bank_payment_views.payment_cancel,
        name="payment_cancel",
    ),
    # RESIDENT room
    path(
        "resident/resident_room_list",
        resident_room_views.room_list,
        name="resident_room_list",
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
    path(
        "resident/notification/",
        resident_notification_history,
        name="resident_notification_history",
    ),
    # ADMIN URL
    path(
        "admin/send-notification/",
        admin_send_notification,
        name="admin_send_notification",
    ),
    path("admin/user_list", admin_user_view.user_list, name="user_list"),
    path("admin/user/create/", admin_user_view.create_user, name="create_user"),
    path(
        "admin/user/update/<str:user_id>",
        admin_user_view.update_user,
        name="update_user",
    ),
    path(
        "admin/user/toggle-active/<str:user_id>/",
        admin_user_view.toggle_active,
        name="toggle_active",
    ),
    path(
        "admin/user/<str:user_id>/delete/",
        admin_user_view.delete_user,
        name="delete_user",
    ),
    path(
        "admin/load_districts/",
        admin_user_view.load_districts,
        name="load_districts",
    ),
    path("admin/load_wards/", admin_user_view.load_wards, name="load_wards"),
    # ADMIN notification
    path(
        "admin/notification/",
        admin_notification_history,
        name="admin_notification_history",
    ),
    # notification for all role
    path(
        "notification/mark-read/<int:notification_id>/",
        mark_notification_read,
        name="mark_notification_read",
    ),
]
