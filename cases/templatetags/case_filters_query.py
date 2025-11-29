from django import template

register = template.Library() # <-- MUST be named 'register'

@register.filter
def filter_by_key(queryset, args):
    # ... your filter code ...
    """
    Allows simple filtering of a QuerySet within a template.
    Usage: queryset|filter_by_key:"key=value"
    """
    if not args:
        return queryset

    try:
        key, value = args.split('=')
        
        # Handle boolean values passed as strings
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False

        filter_kwargs = {key: value}
        return queryset.filter(**filter_kwargs)
    except Exception:
        # Return the original queryset if parsing fails
        return queryset