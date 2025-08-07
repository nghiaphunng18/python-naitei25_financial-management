from django import forms
from django.utils.translation import gettext_lazy as _
from ...models import Role, User
from ...constants import StringLength, STATUS_CHOICES


class UserCreateForm(forms.Form):
    user_id = forms.CharField(
        max_length=StringLength.SHORT.value,
        label=_("ID người dùng"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập ID"),
            }
        ),
    )

    full_name = forms.CharField(
        max_length=StringLength.EXTRA_LONG.value,
        label=_("Họ và tên"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập họ tên"),
            }
        ),
    )
    email = forms.EmailField(
        max_length=StringLength.LONG.value,
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập email"),
            }
        ),
    )
    phone = forms.CharField(
        max_length=StringLength.SHORT.value,
        label=_("Số điện thoại"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập số điện thoại"),
            }
        ),
    )  # nho kiem tra so dien thoai hop le - chi toan so
    detail_address = forms.CharField(
        label=_("Địa chỉ chi tiết"),
        max_length=StringLength.ADDRESS.value,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập địa chỉ chi tiết"),
            }
        ),
    )

    province_name = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Tên tỉnh"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập tên tỉnh"),
            }
        ),
    )
    province_code = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Mã tỉnh"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập mã tỉnh"),
            }
        ),
    )
    district_name = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Tên quận/huyện"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập tên quận/huyện"),
            }
        ),
    )
    district_code = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Mã quận/huyện"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập mã quận/huyện"),
            }
        ),
    )
    ward_name = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Tên phường/xã"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập tên phường/xã"),
            }
        ),
    )
    ward_code = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Mã phường/xã"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập mã phường/xã"),
            }
        ),
    )

    role = forms.ModelChoiceField(
        label=_("Vai trò"),
        queryset=Role.objects.all(),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Chọn vai trò"),
            }
        ),
    )

    status = forms.ChoiceField(
        label=_("Trạng thái"),
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
            }
        ),
    )

    def clean_user_id(self):
        user_id = self.cleaned_data.get("user_id")
        if User.objects.filter(user_id=user_id).exists():
            raise forms.ValidationError(_("ID đã tồn tại."))
        return user_id

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not phone.isdigit():
            raise forms.ValidationError(_("Số điện thoại chỉ được chứa chữ số."))
        return phone

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("Email đã tồn tại."))
        return email


class UserUpdateForm(forms.Form):
    user_id = forms.CharField(
        max_length=StringLength.SHORT.value,
        label=_("Mã người dùng"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md bg-gray-100 cursor-not-allowed shadow-sm focus:outline-none",
                "readonly": "readonly",
            }
        ),
    )

    full_name = forms.CharField(
        max_length=StringLength.EXTRA_LONG.value,
        label=_("Họ và tên"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập họ tên"),
            }
        ),
    )
    email = forms.EmailField(
        max_length=StringLength.LONG.value,
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập email"),
            }
        ),
    )
    phone = forms.CharField(
        max_length=StringLength.SHORT.value,
        label=_("Số điện thoại"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập số điện thoại"),
            }
        ),
    )
    detail_address = forms.CharField(
        label=_("Địa chỉ chi tiết"),
        max_length=StringLength.ADDRESS.value,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập địa chỉ chi tiết"),
            }
        ),
    )

    province_name = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Tên tỉnh"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập tên tỉnh"),
            }
        ),
    )
    province_code = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Mã tỉnh"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập mã tỉnh"),
            }
        ),
    )
    district_name = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Tên quận/huyện"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập tên quận/huyện"),
            }
        ),
    )
    district_code = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Mã quận/huyện"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập mã quận/huyện"),
            }
        ),
    )
    ward_name = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Tên phường/xã"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập tên phường/xã"),
            }
        ),
    )
    ward_code = forms.CharField(
        max_length=StringLength.MEDIUM.value,
        label=_("Mã phường/xã"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập mã phường/xã"),
            }
        ),
    )

    role = forms.ModelChoiceField(
        label=_("Vai trò"),
        queryset=Role.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
            }
        ),
    )

    status = forms.ChoiceField(
        label=_("Trạng thái"),
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
            }
        ),
    )

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not phone.isdigit():
            raise forms.ValidationError(_("Số điện thoại chỉ được chứa chữ số."))
        return phone

    def clean_email(self):
        email = self.cleaned_data.get("email")
        user_id = self.cleaned_data.get("user_id")
        if (
            User.objects.filter(email=email).exclude(user_id=user_id).exists()
        ):  # admin cannot change user_id
            raise forms.ValidationError(_("Email đã tồn tại."))

        return email
