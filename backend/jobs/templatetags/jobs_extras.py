"""
Custom template filters for jobs app
"""
from django import template

register = template.Library()

@register.filter
def percentage(value):
    """Convert decimal value (0.0-1.0) to percentage (0-100)"""
    try:
        return int(float(value) * 100)
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def match_color(value):
    """Return CSS class based on match percentage"""
    try:
        percentage_val = float(value) * 100
        if percentage_val >= 80:
            return 'match-high'
        elif percentage_val >= 60:
            return 'match-medium'
        else:
            return 'match-low'
    except (ValueError, TypeError):
        return 'match-low'

@register.filter
def match_badge_color(value):
    """Return badge color class based on match percentage"""
    try:
        percentage_val = float(value) * 100
        if percentage_val >= 80:
            return 'bg-success'
        elif percentage_val >= 60:
            return 'bg-warning'
        else:
            return 'bg-secondary'
    except (ValueError, TypeError):
        return 'bg-secondary'

@register.filter
def dict_get(dictionary, key):
    """Look up a dictionary value by key in templates. Usage: {{ mydict|dict_get:item.id }}"""
    if dictionary is None:
        return None
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None

@register.filter
def match_pct_color(pct):
    """Return a CSS color class name based on an integer percentage (0-100)"""
    try:
        pct = int(pct)
        if pct >= 75:
            return 'match-pct-high'
        elif pct >= 50:
            return 'match-pct-good'
        elif pct >= 30:
            return 'match-pct-medium'
        else:
            return 'match-pct-low'
    except (ValueError, TypeError):
        return 'match-pct-low'

