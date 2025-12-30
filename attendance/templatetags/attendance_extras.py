from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key."""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def is_in_list(value, the_list):
    """Check if a value is in a list."""
    if the_list is None:
        return False
    return value in the_list
