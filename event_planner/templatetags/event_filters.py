from django import template

register = template.Library()

@register.filter
def indian_number(value):
    try:
        # Remove commas if any exist before parsing
        if isinstance(value, str):
            value = value.replace(',', '')
        value = int(float(value))
    except (ValueError, TypeError):
        return value
        
    s = str(value)
    if len(s) <= 3:
        return s
    
    last_three = s[-3:]
    other_numbers = s[:-3]
    
    other_numbers = other_numbers[::-1]
    chunks = [other_numbers[i:i+2][::-1] for i in range(0, len(other_numbers), 2)]
    chunks.reverse()
    
    return ",".join(chunks) + "," + last_three
