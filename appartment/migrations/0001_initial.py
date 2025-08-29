import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Province",
            fields=[
                ("province_id", models.AutoField(primary_key=True, serialize=False)),
                ("province_name", models.CharField(max_length=30)),
                ("province_code", models.CharField(max_length=30)),
            ],
            options={
                "db_table": "provinces",
            },
        ),
        migrations.CreateModel(
            name="AdditionalService",
            fields=[
                ("service_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("per_room", "Per Room"),
                            ("per_person", "Per Person"),
                        ],
                        default="per_room",
                        max_length=20,
                    ),
                ),
                (
                    "description",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "additional_services",
            },
        ),
        migrations.CreateModel(
            name="ElectricWaterTotal",
            fields=[
                ("total_id", models.AutoField(primary_key=True, serialize=False)),
                ("summary_for_month", models.DateTimeField()),
                ("total_electricity", models.IntegerField()),
                ("total_water", models.IntegerField()),
                (
                    "electricity_cost",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("water_cost", models.DecimalField(decimal_places=2, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "electric_water_totals",
            },
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                ("role_id", models.AutoField(primary_key=True, serialize=False)),
                ("role_name", models.CharField(max_length=30)),
                (
                    "description",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
            ],
            options={
                "db_table": "roles",
            },
        ),
        migrations.CreateModel(
            name="Room",
            fields=[
                (
                    "room_id",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                (
                    "area",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("available", "Available"),
                            ("occupied", "Occupied"),
                            ("maintenance", "Maintenance"),
                            ("unavailable", "Unavailable"),
                        ],
                        default="available",
                        max_length=20,
                    ),
                ),
                ("max_occupants", models.IntegerField(default=5)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "rooms",
            },
        ),
        migrations.CreateModel(
            name="SystemSettings",
            fields=[
                (
                    "setting_key",
                    models.CharField(max_length=50, primary_key=True, serialize=False),
                ),
                ("setting_value", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "system_settings",
            },
        ),
        # Bảng có khóa ngoại đơn giản
        migrations.CreateModel(
            name="District",
            fields=[
                ("district_id", models.AutoField(primary_key=True, serialize=False)),
                ("district_name", models.CharField(max_length=30)),
                ("district_code", models.CharField(max_length=30)),
                (
                    "province",
                    models.ForeignKey(
                        db_column="province_id",
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.province",
                    ),
                ),
            ],
            options={
                "db_table": "districts",
            },
        ),
        migrations.CreateModel(
            name="Ward",
            fields=[
                ("ward_id", models.AutoField(primary_key=True, serialize=False)),
                ("ward_name", models.CharField(max_length=30)),
                ("ward_code", models.CharField(max_length=30)),
                (
                    "district",
                    models.ForeignKey(
                        db_column="district_id",
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.district",
                    ),
                ),
            ],
            options={
                "db_table": "wards",
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "user_id",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("full_name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=50, unique=True)),
                ("phone", models.CharField(max_length=20)),
                (
                    "detail_address",
                    models.CharField(blank=True, max_length=55, null=True),
                ),
                ("is_active", models.IntegerField(default=1)),
                ("is_deleted", models.IntegerField(default=0)),
                ("is_staff", models.IntegerField(default=0)),
                ("is_superuser", models.IntegerField(default=0)),
                (
                    "date_joined",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "district",
                    models.ForeignKey(
                        blank=True,
                        db_column="district_id",
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.district",
                    ),
                ),
                (
                    "province",
                    models.ForeignKey(
                        blank=True,
                        db_column="province_id",
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.province",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        db_column="role_id",
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.role",
                    ),
                ),
                (
                    "ward",
                    models.ForeignKey(
                        blank=True,
                        db_column="ward_id",
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.ward",
                    ),
                ),
            ],
            options={
                "db_table": "users",
            },
        ),
        migrations.CreateModel(
            name="Bill",
            fields=[
                ("bill_id", models.AutoField(primary_key=True, serialize=False)),
                ("bill_month", models.DateTimeField()),
                (
                    "electricity_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "water_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "additional_service_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "total_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("unpaid", "Unpaid"),
                            ("paid", "Paid"),
                            ("overdue", "Overdue"),
                        ],
                        default="unpaid",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("due_date", models.DateTimeField(blank=True, null=True)),
                (
                    "room",
                    models.ForeignKey(
                        db_column="room_id",
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.room",
                    ),
                ),
            ],
            options={
                "db_table": "bills",
            },
        ),
        # Bảng có khóa ngoại phức tạp hơn
        migrations.CreateModel(
            name="DraftBill",
            fields=[
                ("draft_bill_id", models.AutoField(primary_key=True, serialize=False)),
                ("bill_month", models.DateField()),
                (
                    "draft_type",
                    models.CharField(
                        choices=[
                            ("ELECTRIC_WATER", "Điện & Nước"),
                            ("SERVICES", "Dịch vụ"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("DRAFT", "Nháp"),
                            ("SENT", "Đã gửi"),
                            ("CONFIRMED", "Đã xác nhận"),
                            ("REJECTED", "Đã từ chối"),
                        ],
                        default="DRAFT",
                        max_length=20,
                    ),
                ),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("details", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "room",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="appartment.room",
                    ),
                ),
            ],
            options={
                "db_table": "draft_bills",
                "unique_together": {("room", "bill_month", "draft_type")},
            },
        ),
        migrations.CreateModel(
            name="MonthlyMeterReading",
            fields=[
                ("service_id", models.AutoField(primary_key=True, serialize=False)),
                ("service_month", models.DateTimeField()),
                ("electricity_index", models.IntegerField(blank=True, null=True)),
                ("water_index", models.IntegerField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("confirmed", "Confirmed"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "room",
                    models.ForeignKey(
                        db_column="room_id",
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.room",
                    ),
                ),
            ],
            options={
                "db_table": "monthly_meter_readings",
            },
        ),
        migrations.CreateModel(
            name="RentalPrice",
            fields=[
                (
                    "rental_price_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "effective_date",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "room",
                    models.ForeignKey(
                        db_column="room_id",
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="rental_prices",
                        to="appartment.room",
                    ),
                ),
            ],
            options={
                "db_table": "rental_prices",
            },
        ),
        migrations.CreateModel(
            name="RoomResident",
            fields=[
                (
                    "room_resident_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("move_in_date", models.DateTimeField(auto_now_add=True)),
                ("move_out_date", models.DateTimeField(blank=True, null=True)),
                (
                    "room",
                    models.ForeignKey(
                        db_column="room_id",
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="residents",
                        to="appartment.room",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        db_column="user_id",
                        db_constraint=False,
                        on_delete=django.db.models.deletion.RESTRICT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "room_resident",
            },
        ),
        migrations.CreateModel(
            name="BillAdditionalService",
            fields=[
                (
                    "bill_additional_service_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("service_month", models.DateTimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("confirmed", "Confirmed"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "additional_service",
                    models.ForeignKey(
                        db_column="additional_service_id",
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.additionalservice",
                    ),
                ),
                (
                    "bill",
                    models.ForeignKey(
                        blank=True,
                        db_column="bill_id",
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.bill",
                    ),
                ),
                (
                    "room",
                    models.ForeignKey(
                        blank=True,
                        db_column="room_id",
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="appartment.room",
                    ),
                ),
            ],
            options={
                "db_table": "bill_additional_services",
            },
        ),
        migrations.CreateModel(
            name="PaymentHistory",
            fields=[
                ("payment_id", models.AutoField(primary_key=True, serialize=False)),
                ("order_code", models.BigIntegerField(blank=True, null=True)),
                ("payment_date", models.DateTimeField(blank=True, null=True)),
                ("amount_paid", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("cash", "Cash"),
                            ("bank_transfer", "Bank Transfer"),
                            ("card", "Card"),
                        ],
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True, null=True)),
                (
                    "transaction_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PENDING", "Pending"),
                            ("SUCCESS", "Success"),
                            ("FAILED", "Failed"),
                        ],
                        default=None,
                        max_length=20,
                        null=True,
                    ),
                ),
                (
                    "bill",
                    models.ForeignKey(
                        blank=True,
                        db_column="bill_id",
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="payment_history",
                        to="appartment.bill",
                    ),
                ),
                (
                    "processed_by",
                    models.ForeignKey(
                        blank=True,
                        db_column="processed_by",
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "payment_history",
            },
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "notification_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("title", models.CharField(max_length=100)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("unread", "Unread"), ("read", "Read")],
                        default="unread",
                        max_length=20,
                    ),
                ),
                (
                    "receiver",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="received_notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="sent_notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "notifications",
                "indexes": [
                    models.Index(
                        fields=["sender"], name="notificatio_sender__893501_idx"
                    ),
                    models.Index(
                        fields=["receiver"], name="notificatio_receive_61b4e9_idx"
                    ),
                    models.Index(
                        fields=["created_at"], name="notificatio_created_e4c995_idx"
                    ),
                    models.Index(
                        fields=["status"], name="notificatio_status_fce6f5_idx"
                    ),
                ],
            },
        ),
    ]
