from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def querystring_with_page(context, page_number, remove=None):
    """
    Generate a query string with the given page number and current GET params.
    Optionally remove specific parameters by passing a comma-separated 'remove' string.
    Usage:
        {% querystring_with_page 2 %}
        {% querystring_with_page 1 "subject,difficulty" %}
    """
    request = context['request']
    query_params = request.GET.copy()
    
    # Remove unwanted keys if any
    if remove:
        for key in remove.split(','):
            query_params.pop(key.strip(), None)

    query_params['page'] = page_number
    return '?' + urlencode(query_params, doseq=True)
