# core/templatetags/form_filters.py
from django import template
from django.forms import CheckboxSelectMultiple, RadioSelect

register = template.Library()

@register.filter(name='is_a')
def is_a(field, class_names_str):
    """
    Custom template filter to check if a form widget is of a certain class.
    Usage: {% if field.field.widget|is_a:"RadioSelect,CheckboxSelectMultiple" %}
    """
    class_names = class_names_str.split(',')
    widget_class_name = field.__class__.__name__
    return widget_class_name in class_names

# In core/templatetags/form_filters.py

# ... (the 'register =' and 'is_a' function stay the same) ...

@register.filter(name='add_class')
def add_class(field_tag, css_class):
    """
    Adds a CSS class to a Django form field's HTML tag.
    This filter works on a pre-rendered HTML string.
    """
    # We are working with a string, not a field object.
    # We'll inject the class attribute right before the closing '>'.
    return field_tag.replace('>', f' class="{css_class}">', 1)