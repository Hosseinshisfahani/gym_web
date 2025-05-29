from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    # Check if this is a form field with as_widget method
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={"class": css_class})
    # If it's a string or other type, just return it unchanged
    return field

@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using its key"""
    return dictionary.get(key) 