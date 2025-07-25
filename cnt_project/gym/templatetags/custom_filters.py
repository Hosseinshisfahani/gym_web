from django import template
import jdatetime
from datetime import datetime, date

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
def subtract(value, arg):
    """Subtract the argument from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using its key"""
    return dictionary.get(key)

@register.filter
def add_commas(value):
    """Add commas to numbers for formatting (e.g., 1000 -> 1,000)"""
    try:
        # Convert to integer to remove decimal places
        num = int(float(value))
        # Format with commas
        return f"{num:,}"
    except (ValueError, TypeError):
        return value

@register.filter
def format_price(value):
    """Format numbers with slash separators (e.g., 500000 -> 500/000)"""
    try:
        # Convert to integer to remove decimal places
        num = int(float(value))
        # Convert to string and reverse it for easier processing
        num_str = str(num)[::-1]
        # Add slashes every 3 digits
        formatted = '/'.join([num_str[i:i+3] for i in range(0, len(num_str), 3)])
        # Reverse it back
        return formatted[::-1]
    except (ValueError, TypeError):
        return value 

@register.filter
def persian_date(value, format_string='Y/m/d'):
    """Convert Gregorian date to Persian (Jalali) date"""
    if not value:
        return ""
    
    try:
        # Handle both datetime and date objects
        if isinstance(value, datetime):
            persian_dt = jdatetime.datetime.fromgregorian(datetime=value)
        elif isinstance(value, date):
            persian_dt = jdatetime.date.fromgregorian(date=value)
        else:
            return str(value)
        
        # Map format codes to Persian equivalents
        if format_string == 'Y/m/d':
            return f"{persian_dt.year}/{persian_dt.month:02d}/{persian_dt.day:02d}"
        elif format_string == 'j F Y':
            # Persian month names
            persian_months = [
                '', 'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
            ]
            month_name = persian_months[persian_dt.month] if persian_dt.month <= 12 else str(persian_dt.month)
            return f"{persian_dt.day} {month_name} {persian_dt.year}"
        elif format_string == 'j F':
            persian_months = [
                '', 'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
            ]
            month_name = persian_months[persian_dt.month] if persian_dt.month <= 12 else str(persian_dt.month)
            return f"{persian_dt.day} {month_name}"
        else:
            # Default format
            return f"{persian_dt.year}/{persian_dt.month:02d}/{persian_dt.day:02d}"
            
    except Exception as e:
        # If conversion fails, return original value
        return str(value)