from django import template

register = template.Library()

@register.filter
def get_item(obj, key):
    if isinstance(obj, dict):
        return obj.get(key)
    
    if isinstance(obj, list):
        try:
            return obj[int(key)]
        except (ValueError, IndexError, TypeError):
            return None
            
    return None

@register.filter
def subtract(value, arg):
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def split(value, arg):
    return value.split(arg)

@register.filter
def filter_status(queryset, status):
    if not queryset:
        return []
    return [item for item in queryset if item.status == status]
