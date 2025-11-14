from django import template
from django.utils import timezone
from datetime import datetime

register = template.Library()

@register.filter(name='days_until')
def days_until(value):
    """Calculate days remaining until a given date"""
    if not value:
        return 0
    
    # Ensure both datetimes are timezone-aware
    now = timezone.now()
    
    # If value is naive, make it aware
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    
    # Calculate difference
    delta = value - now
    
    # Return days (can be negative if expired)
    return delta.days
