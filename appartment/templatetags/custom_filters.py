# templatetags/custom_filters.py
from django import template
from django.utils.translation import gettext as _

register = template.Library()

# Debug: In ra để kiểm tra filter có được load không
print("Custom filters loaded successfully!")


@register.filter
def room_occupancy_status(room, current_occupants):
    """
    Trả về dict chứa thông tin trạng thái phòng dựa vào số người hiện tại
    Usage: {{ room|room_occupancy_status:current_occupants }}

    Args:
        room: Room object có thuộc tính max_occupants
        current_occupants: Số người hiện tại trong phòng

    Returns:
        dict: {
            'text': str - Văn bản hiển thị,
            'css_class': str - CSS class cho text,
            'icon_class': str - CSS class cho icon
        }
    """
    if current_occupants == 0:
        return {
            "text": _("Trống"),
            "css_class": "text-green-600",
            "icon_class": "text-green-400",
        }
    elif current_occupants >= room.max_occupants:
        return {
            "text": _("Đầy"),
            "css_class": "text-red-600",
            "icon_class": "text-red-400",
        }
    else:
        return {
            "text": _("Còn chỗ"),
            "css_class": "text-blue-600",
            "icon_class": "text-blue-400",
        }


@register.filter
def format_date_dmy(date):
    """
    Format date theo định dạng dd/mm/yyyy
    Usage: {{ date|format_date_dmy }}
    """
    if date:
        return date.strftime("%d/%m/%Y")
    return ""


@register.filter
def occupancy_percentage(current_occupants, max_occupants):
    """
    Tính phần trăm lấp đầy phòng
    Usage: {{ current_occupants|occupancy_percentage:max_occupants }}
    """
    if max_occupants > 0:
        return (current_occupants / max_occupants) * 100
    return 0


@register.filter
def occupancy_bar_color(occupancy_rate):
    """
    Trả về CSS class cho thanh progress bar dựa vào tỷ lệ lấp đầy
    Usage: {{ occupancy_rate|occupancy_bar_color }}
    """
    if occupancy_rate < 50:
        return "bg-green-500"
    elif occupancy_rate < 80:
        return "bg-yellow-500"
    else:
        return "bg-red-500"


@register.filter
def room_status_options(value, current_status=None):
    """
    Trả về danh sách các option cho room status filter
    Usage: {{ ''|room_status_options:current_filters.status }}
    """
    options = [
        {
            "value": "",
            "text": _("Tất cả trạng thái"),
            "selected": not current_status,
        },
        {
            "value": "available",
            "text": _("Có thể thuê"),
            "selected": current_status == "available",
        },
        {
            "value": "occupied",
            "text": _("Đã thuê"),
            "selected": current_status == "occupied",
        },
        {
            "value": "maintenance",
            "text": _("Bảo trì"),
            "selected": current_status == "maintenance",
        },
        {
            "value": "unavailable",
            "text": _("Không khả dụng"),
            "selected": current_status == "unavailable",
        },
    ]
    return options


@register.filter
def occupancy_filter_options(value, current_occupancy=None):
    """
    Trả về danh sách các option cho occupancy filter
    Usage: {{ ''|occupancy_filter_options:current_filters.occupancy }}
    """
    options = [
        {"value": "", "text": _("Tất cả"), "selected": not current_occupancy},
        {
            "value": "empty",
            "text": _("Trống"),
            "selected": current_occupancy == "empty",
        },
        {
            "value": "partial",
            "text": _("Còn chỗ"),
            "selected": current_occupancy == "partial",
        },
        {
            "value": "full",
            "text": _("Đầy"),
            "selected": current_occupancy == "full",
        },
    ]
    return options


@register.filter
def area_filter_options(value, current_area=None):
    """
    Trả về danh sách các option cho area filter
    Usage: {{ ''|area_filter_options:current_filters.area }}
    """
    options = [
        {
            "value": "",
            "text": _("Tất cả diện tích"),
            "selected": not current_area,
        },
        {
            "value": "small",
            "text": _("< 20m²"),
            "selected": current_area == "small",
        },
        {
            "value": "medium",
            "text": _("20-50m²"),
            "selected": current_area == "medium",
        },
        {
            "value": "large",
            "text": _("> 50m²"),
            "selected": current_area == "large",
        },
    ]
    return options


@register.filter
def max_occupants_filter_options(value, current_max_occupants=None):
    """
    Trả về danh sách các option cho max occupants filter
    Usage: {{ ''|max_occupants_filter_options:current_filters.max_occupants }}
    """
    options = [
        {
            "value": "",
            "text": _("Tất cả"),
            "selected": not current_max_occupants,
        },
        {
            "value": "small",
            "text": _("1-2 người"),
            "selected": current_max_occupants == "small",
        },
        {
            "value": "medium",
            "text": _("3-5 người"),
            "selected": current_max_occupants == "medium",
        },
        {
            "value": "large",
            "text": _("> 5 người"),
            "selected": current_max_occupants == "large",
        },
    ]
    return options
