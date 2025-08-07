from django import template
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext as _

register = template.Library()


@register.simple_tag
def user_status_button(is_active):
    if is_active:
        return format_html(
            '<button type="submit" class="py-1 px-2 bg-green-400 text-white rounded-md hover:bg-green-500">'
            '<i class="fa-solid fa-user-check"></i>'
            "</button>"
        )
    else:
        return format_html(
            '<button type="submit" class="py-1 px-2 bg-yellow-400 text-white rounded-md hover:bg-yellow-500">'
            '<i class="fa-solid fa-user-xmark"></i>'
            "</button>"
        )


@register.simple_tag(takes_context=True)
def render_pagination_simple(context, page_obj, query_param="page", anchor=""):
    if not page_obj:
        return ""

    request = context["request"]  # context processor request
    base_params = request.GET.copy()

    parts = []
    # previous
    if page_obj.has_previous():
        prev_params = base_params.copy()
        prev_params[query_param] = page_obj.previous_page_number()
        parts.append(format_html(
            '<a href="?{}{}" class="px-3 py-1 mx-1 bg-gray-200 rounded hover:bg-gray-300">{}</a>',
            prev_params.urlencode(), anchor, _("previous")
        ))

    # current
    parts.append(format_html(
        '<span class="px-3 py-1 font-semibold">{0} / {1}</span>',
        page_obj.number, page_obj.paginator.num_pages
    ))

    # next
    if page_obj.has_next():
        next_params = base_params.copy()
        next_params[query_param] = page_obj.next_page_number()
        parts.append(format_html(
            '<a href="?{}{}" class="px-3 py-1 mx-1 bg-gray-200 rounded hover:bg-gray-300">{}</a>',
            next_params.urlencode(), anchor, _("next")
        ))

    return format_html(
        '<div class="flex justify-center mt-4">{}</div>',
        format_html_join("", "{}", ((p,) for p in parts)),
    )
