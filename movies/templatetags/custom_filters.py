from django import template


register = template.Library()

@register.filter
def to_char(value):
    try:
        return chr(int(value))
    except:
        return ''

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key)