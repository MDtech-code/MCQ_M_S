from django import template
from datetime import datetime

register = template.Library()

@register.filter
def parse_iso_date(value):
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None