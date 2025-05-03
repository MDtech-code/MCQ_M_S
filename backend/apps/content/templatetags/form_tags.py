from django.template import Library

register = Library()

@register.filter
def default(value, arg):
    return value if value else arg


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key) if dictionary else None


@register.filter
def lookup(dictionary, key):
    return dictionary.get(key)

@register.filter
def attr(obj, attribute):
    """Retrieve an attribute from an object."""
    return getattr(obj, attribute, None)


@register.filter
def sub(value, arg):
    """Subtract arg from value."""
    return value - arg if value is not None and arg is not None else 0

@register.filter
def div(value, arg):
    """Divide value by arg, avoiding division by zero."""
    return value / arg if value is not None and arg else 0

@register.filter
def mul(value, arg):
    """Multiply value by arg."""
    return value * arg if value is not None and arg is not None else 0
