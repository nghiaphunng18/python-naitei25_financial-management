import json
from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe
from django.db.models.query import QuerySet
from django.db.models import Model


# Định nghĩa một Encoder tùy chỉnh để xử lý các đối tượng Model và QuerySet
class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, QuerySet):
            # Nếu là một QuerySet, chuyển nó thành một list các dictionary
            return list(obj.values())
        if isinstance(obj, Model):
            # Nếu là một Model, chuyển nó thành một dictionary
            # Bạn có thể tùy chỉnh các trường muốn lấy ở đây
            return {
                "pk": obj.pk,
                "description": getattr(obj, "description", str(obj)),
                # Thêm các trường khác nếu cần
            }
        return super().default(obj)


register = template.Library()


@register.filter
def to_json(value):
    """
    Chuyển đổi một dictionary/object Python thành một chuỗi JSON an toàn
    sử dụng bộ mã hóa tùy chỉnh để xử lý các đối tượng Django.
    """
    return mark_safe(json.dumps(value, cls=CustomJSONEncoder))
