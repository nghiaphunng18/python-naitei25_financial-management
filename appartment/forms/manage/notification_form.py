from django import forms
from django.utils.translation import gettext_lazy as _
from ...models import User
from ...constants import UserRole


class NotificationForm(forms.Form):
    receiver_type = forms.ChoiceField(
        choices=[
            ("admin", _("Admin")),
            ("manager", _("Quản lý")),
            ("resident", _("Cư dân")),
        ],
        label=_("Gửi cho"),
        widget=forms.Select(
            attrs={"class": "w-full p-2 border rounded", "id": "id_receiver_type"}
        ),
        required=False,
        initial="resident",  # default
    )
    send_all = forms.BooleanField(
        label=_("Gửi tất cả"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "mr-2", "id": "id_send_all"}),
    )

    title = forms.CharField(
        max_length=100,
        label=_("Tiêu đề"),
        widget=forms.TextInput(attrs={"class": "w-full p-2 border rounded"}),
        required=True,
    )
    message = forms.CharField(
        label=_("Nội dung"),
        widget=forms.Textarea(attrs={"class": "w-full p-2 border rounded", "rows": 4}),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.sender_role = kwargs.pop("sender_role", None)
        super().__init__(*args, **kwargs)

        if self.sender_role == UserRole.RESIDENT.value:
            del self.fields["receiver_type"]
            del self.fields["send_all"]
        else:
            self.fields["receiver_type"].required = True

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
