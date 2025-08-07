from django.utils.translation import gettext_lazy as _
from django import forms

from appartment.constants import DecimalConfig, MIN_RENTAL_PRICE


class RentalPriceCreateForm(forms.Form):
    price = forms.DecimalField(
        min_value=MIN_RENTAL_PRICE,
        **DecimalConfig.MONEY,
        widget=forms.NumberInput(
            attrs={
                "placeholder": _("Nhập giá thuê"),
                "step": "10000",
                "min": "0",
                "class": "border border-blue-300 p-2 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
            }
        ),
    )

    effective_date = forms.DateTimeField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "border border-blue-300 p-2 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
            }
        ),
    )


class RentalPriceUpdateForm(forms.Form):
    price = forms.DecimalField(
        min_value=MIN_RENTAL_PRICE,
        **DecimalConfig.MONEY,
    )

    effective_date = forms.DateField()
