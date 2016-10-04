from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@stringfilter
@register.filter(name='escape_quotes')
def escape_quotes(value):
	value = value.decode("utf-8")
	escape_single_quotes = value.replace("'", "\\'")
	escape_single_and_double_quotes = escape_single_quotes.replace('"', '\\"')

	return escape_single_and_double_quotes