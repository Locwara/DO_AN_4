from django import template

register = template.Library()

@register.filter
def last_id(messages_list):
    if messages_list:
        # Kiểm tra xem là QuerySet hay list
        if hasattr(messages_list, 'last'):
            # Là QuerySet
            return messages_list.last().id
        else:
            # Là list
            return messages_list[-1].id if messages_list else 0
    return 0