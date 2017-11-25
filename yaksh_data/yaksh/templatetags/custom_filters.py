from django import template
from django.template.defaultfilters import stringfilter
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

register = template.Library()

@stringfilter
@register.filter(name='escape_quotes')
def escape_quotes(value):
	value = value.decode("utf-8")
	escape_single_quotes = value.replace("'", "\\'")
	escape_single_and_double_quotes = escape_single_quotes.replace('"', '\\"')

	return escape_single_and_double_quotes

@register.assignment_tag(name="completed")
def completed(answerpaper):
	return answerpaper.filter(status="completed").count()

@register.assignment_tag(name="inprogress")
def inprogress(answerpaper):
	return answerpaper.filter(status="inprogress").count()

@register.filter(name='zip')
def zip_longest_out(a, b):
	return zip_longest(a, b)
