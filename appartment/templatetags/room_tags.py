from django import template
from django.utils.html import format_html
from django.utils.translation import gettext as _
from django.urls import reverse

register = template.Library()


@register.simple_tag
def status_badge(status):
    if status == "Đang ở":
        return format_html(
            '<span class="bg-green-100 text-green-800 text-sm font-semibold px-3 py-1 rounded-full">{}</span>',
            status,
        )
    else:
        return format_html(
            '<span class="bg-red-100 text-red-800 text-sm font-semibold px-3 py-1 rounded-full">{}</span>',
            status,
        )


@register.simple_tag
def back_link(url_name, *args, **kwargs):
    """
    Nút quay lại.
    """
    url = reverse(url_name, args=args, kwargs=kwargs)
    text = _("Quay lại")
    return format_html(
        """
        <a href="{}" class="inline-flex items-center px-4 py-2 text-gray-600 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition duration-200">
            <i class="fa-solid fa-arrow-left mr-2"></i>
            <span>{}</span>
        </a>
        """,
        url,
        text,
    )
