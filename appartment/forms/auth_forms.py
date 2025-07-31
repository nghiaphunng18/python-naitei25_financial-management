from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import User
from ..constants import StringLength


class LoginForm(forms.Form):
    """
    User login form
    """

    email = forms.EmailField(
        max_length=StringLength.LONG.value,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Nhập email của bạn"),
                "autofocus": True,
                "required": True,
            }
        ),
        label=_("Email"),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Nhập mật khẩu"),
                "required": True,
            }
        ),
        label=_("Mật khẩu"),
    )

    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Ghi nhớ đăng nhập"),
    )

    def clean(self):
        """
        Validate form data
        """
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = User.objects.filter(email=email).first()
            if not user:
                raise forms.ValidationError(
                    _("Email hoặc mật khẩu không chính xác.")
                )
            if not user.is_active:
                raise forms.ValidationError(
                    _("Tài khoản này đã bị vô hiệu hóa.")
                )

        return cleaned_data
