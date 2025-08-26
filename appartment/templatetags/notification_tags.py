from django import template

register = template.Library()


@register.inclusion_tag("partials/menu_notification.html", takes_context=True)
def notification_menu_item(context, url_name, label="Gửi thông báo"):
    request = context["request"]
    return {
        "url_name": url_name,
        "label": label,
        "active": request.resolver_match.url_name == url_name,
    }
