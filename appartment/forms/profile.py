from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from ..models import User
import re


class UserProfileForm(forms.ModelForm):
    phone_validator = RegexValidator(
        regex=r"^(\+84|0)(3[2-9]|5[689]|7[06-9]|8[1-689]|9[0-46-9])[0-9]{7}$",
        message=_(
            "Số điện thoại không hợp lệ. Vui lòng nhập số điện thoại Việt Nam hợp lệ (VD: 0912345678 hoặc +84912345678)"
        ),
    )

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
                "placeholder": "example@email.com",
            }
        ),
        error_messages={
            "required": _("Email là bắt buộc."),
            "invalid": _("Vui lòng nhập email hợp lệ."),
        },
    )

    phone = forms.CharField(
        max_length=15,
        validators=[phone_validator],
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
                "placeholder": "0912345678",
            }
        ),
        error_messages={"required": _("Số điện thoại là bắt buộc.")},
    )

    class Meta:
        model = User
        fields = ["email", "phone"]

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        # Add original values to detect changes
        if self.user_instance:
            self.original_email = self.user_instance.email
            self.original_phone = self.user_instance.phone

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if not email:
            raise forms.ValidationError(_("Email là bắt buộc."))

        # Check if email is unique (exclude current user)
        if self.user_instance:
            existing_user = (
                User.objects.filter(email=email)
                .exclude(pk=self.user_instance.pk)
                .first()
            )
        else:
            existing_user = User.objects.filter(email=email).first()

        if existing_user:
            raise forms.ValidationError(
                _("Email này đã được sử dụng bởi tài khoản khác.")
            )

        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")

        if not phone:
            raise forms.ValidationError(_("Số điện thoại là bắt buộc."))

        # Normalize phone number (remove spaces, dashes)
        phone = re.sub(r"[\s\-\(\)]", "", phone)

        # Convert +84 to 0 for consistency
        if phone.startswith("+84"):
            phone = "0" + phone[3:]

        return phone

    def has_changed(self):
        """Check if any field has been modified"""
        if not self.user_instance:
            return True

        return (
            self.cleaned_data.get("email") != self.original_email
            or self.cleaned_data.get("phone") != self.original_phone
        )
