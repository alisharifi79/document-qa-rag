from django import template
import re

register = template.Library()

PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")


@register.filter(name="text_direction")
def text_direction(value):
    if not value:
        return "ltr"

    value = str(value)

    if PERSIAN_RE.search(value):
        return "rtl"

    return "ltr"