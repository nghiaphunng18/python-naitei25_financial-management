from django import forms
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from appartment.models.districts import District
from appartment.models.provinces import Province
from appartment.models.wards import Ward
from ...models import Role, User
from ...constants import StringLength, STATUS_CHOICES


class UserCreateForm(forms.Form):
    user_id = forms.CharField(
        max_length=StringLength.SHORT.value,
        label=_("ID người dùng:"),
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
        label=_("Họ và tên:"),
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
        label=_("Email:"),
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
        label=_("Số điện thoại:"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập số điện thoại"),
            }
        ),
    )

    province = forms.ModelChoiceField(
        label=_("Tỉnh/thành phố:"),
        queryset=Province.objects.all(),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "hx-get": reverse_lazy("load_districts"),
                "hx-target": "#id_district",
                "hx-trigger": "change",
                "onchange": "onProvinceChange()",
            }
        ),
    )

    district = forms.ModelChoiceField(
        label=_("Quận/huyện:"),
        queryset=District.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "hx-get": reverse_lazy("load_wards"),
                "hx-target": "#id_ward",
                "hx-trigger": "change",
                "onchange": "onDistrictChange()",
            }
        ),
    )

    ward = forms.ModelChoiceField(
        label=_("Phường/xã:"),
        queryset=Ward.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
            }
        ),
    )

    detail_address = forms.CharField(
        label=_("Địa chỉ chi tiết:"),
        max_length=StringLength.ADDRESS.value,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập địa chỉ chi tiết"),
            }
        ),
    )

    role = forms.ModelChoiceField(
        label=_("Vai trò:"),
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
        label=_("Trạng thái:"),
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "province" in self.data:
            province_id = self.data.get("province")
            self.fields["district"].queryset = District.objects.filter(
                province_id=province_id
            ).order_by("district_name")

        if "district" in self.data:
            district_id = self.data.get("district")
            self.fields["ward"].queryset = Ward.objects.filter(
                district_id=district_id
            ).order_by("ward_name")

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

    def clean_district(self):
        district = self.cleaned_data.get("district")
        province = self.cleaned_data.get("province")

        if district and province and district.province_id != province.province_id:
            raise forms.ValidationError(
                _(
                    "Quận/Huyện '%(district)s' không thuộc Tỉnh/Thành phố'%(province)s'."
                ),
                params={"district": district, "province": province},
            )
        return district

    def clean_ward(self):
        ward = self.cleaned_data.get("ward")
        district = self.cleaned_data.get("district")

        if ward and district and ward.district_id != district.district_id:
            raise forms.ValidationError(
                _("Phường/Xã '%(ward)s' không thuộc Quận/Huyện '%(district)s'."),
                params={"ward": ward, "district": district},
            )
        return ward


class UserUpdateForm(forms.Form):
    user_id = forms.CharField(
        max_length=StringLength.SHORT.value,
        label=_("ID người dùng:"),
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
        label=_("Họ và tên:"),
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
        label=_("Email:"),
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
        label=_("Số điện thoại:"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập số điện thoại"),
            }
        ),
    )

    province = forms.ModelChoiceField(
        label=_("Tỉnh/thành phố:"),
        queryset=Province.objects.all(),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "hx-get": reverse_lazy("load_districts"),
                "hx-target": "#id_district",
                "hx-trigger": "change",
                "onchange": "onProvinceChange()",
            }
        ),
    )

    district = forms.ModelChoiceField(
        label=_("Quận/huyện:"),
        queryset=District.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "hx-get": reverse_lazy("load_wards"),
                "hx-target": "#id_ward",
                "hx-trigger": "change",
                "onchange": "onDistrictChange()",
            }
        ),
    )

    ward = forms.ModelChoiceField(
        label=_("Phường/xã:"),
        queryset=Ward.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
            }
        ),
    )

    detail_address = forms.CharField(
        label=_("Địa chỉ chi tiết:"),
        max_length=StringLength.ADDRESS.value,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
                "placeholder": _("Nhập địa chỉ chi tiết"),
            }
        ),
    )

    role = forms.ModelChoiceField(
        label=_("Vai trò:"),
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
        label=_("Trạng thái:"),
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "border border-gray-300 p-2 w-full rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Take initial in form update
        initial = kwargs.get("initial", {})

        province = initial.get("province") or self.data.get("province")
        district = initial.get("district") or self.data.get("district")

        # If province exists, filter district
        if province:
            self.fields["district"].queryset = District.objects.filter(
                province=province
            )

        # If district exists, filter ward
        if district:
            self.fields["ward"].queryset = Ward.objects.filter(district=district)

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

    def clean_district(self):
        district = self.cleaned_data.get("district")
        province = self.cleaned_data.get("province")

        if district and province and district.province_id != province.province_id:
            raise forms.ValidationError(
                _(
                    "Quận/Huyện '%(district)s' không thuộc Tỉnh/Thành phố'%(province)s'."
                ),
                params={"district": district, "province": province},
            )
        return district

    def clean_ward(self):
        ward = self.cleaned_data.get("ward")
        district = self.cleaned_data.get("district")

        if ward and district and ward.district_id != district.district_id:
            raise forms.ValidationError(
                _("Phường/Xã '%(ward)s' không thuộc Quận/Huyện '%(district)s'."),
                params={"ward": ward, "district": district},
            )
        return ward
