# rooms/templatetags/custom_filters.py
from django import template

register = template.Library()


@register.filter
def format_date_dmy(value):
    """
    Định dạng ngày theo dd/mm/yyyy.
    Có thể dùng cho datetime hoặc date object.
    """
    if value:
        return value.strftime("%d/%m/%Y")
    return ""
