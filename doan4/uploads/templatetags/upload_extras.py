from django import template

register = template.Library()

@register.filter
def get_at_index(list_or_tuple, index):
    """
    Returns the item at the given index from a list or tuple.
    Useful for accessing elements from zipped iterables in templates.
    """
    try:
        return list_or_tuple[index]
    except (IndexError, TypeError):
        return None

@register.filter
def get_item(dictionary, key):
    """
    Returns the value for the given key from a dictionary.
    """
    return dictionary.get(key)
