from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from ..constants import StringLength


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email là bắt buộc")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser phải có is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser phải có is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser):
    user_id = models.CharField(max_length=StringLength.SHORT.value, primary_key=True)
    full_name = models.CharField(max_length=StringLength.EXTRA_LONG.value)
    email = models.EmailField(max_length=StringLength.LONG.value, unique=True)
    phone = models.CharField(max_length=StringLength.SHORT.value)
    role = models.ForeignKey("Role", on_delete=models.RESTRICT, db_column="role_id")
    province = models.ForeignKey(
        "Province",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        db_column="province_id",
    )
    district = models.ForeignKey(
        "District",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        db_column="district_id",
    )
    ward = models.ForeignKey(
        "Ward",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        db_column="ward_id",
    )
    detail_address = models.CharField(
        max_length=StringLength.ADDRESS.value, null=True, blank=True
    )

    # Các trường bắt buộc cho Django authentication
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.full_name

    def get_full_name(self):
        return self.full_name

    # Implement permission methods manually (không dùng PermissionsMixin)
    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_active and self.is_superuser

    objects = UserManager()

    USERNAME_FIELD = "email"  # Sử dụng email để đăng nhập
    REQUIRED_FIELDS = ["full_name"]  # Các trường bắt buộc khi tạo superuser

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.full_name

    def get_full_name(self):
        return self.full_name
