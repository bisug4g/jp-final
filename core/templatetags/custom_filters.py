from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key)

@register.filter
def ordinal(value):
    """Convert integer to ordinal string (1st, 2nd, 3rd, etc.)"""
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value
    
    if 10 <= value % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    return f"{value}{suffix}"


@register.filter
def month_name(value):
    """Convert month number to month name"""
    import calendar
    try:
        return calendar.month_name[int(value)]
    except (ValueError, TypeError, IndexError):
        return value


@register.filter
def format_minute(value):
    """Format minute with leading zero"""
    try:
        return f"{int(value):02d}"
    except (ValueError, TypeError):
        return value
