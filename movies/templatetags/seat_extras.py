from django import template
import builtins   # ✅ important

register = template.Library()

@register.filter(name='chr')
def to_char(value):
    try:
        return builtins.chr(int(value))  # ✅ Use built-in chr
    except:
        return ''