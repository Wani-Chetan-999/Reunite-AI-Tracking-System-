# police/templatetags/case_filters.py

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def get_urgency_color(value):
    """Maps urgency string (High, Medium, Normal) to a Bootstrap color class."""
    value = value.lower()
    if value == 'high':
        return 'danger'
    if value == 'medium':
        return 'warning'
    return 'secondary'  # For 'normal' or default cases

@register.filter
def is_greater_than(value1, value2):
    """Checks if value1 > value2 (Used for timestamp comparisons)."""
    # This works reliably for Python datetime objects, floats, or integers.
    return value1 > value2