from django import template
from django.template.defaultfilters import stringfilter
import os
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


@register.filter(name="file_title")
def file_title(name):
    return os.path.basename(name)


@register.simple_tag
def get_unit_status(course, module, unit, user):
    return course.get_unit_completion_status(module, user, unit)


@register.simple_tag
def get_module_status(user, module, course):
    return module.get_status(user, course)


@register.simple_tag
def get_course_details(course):
    return course.get_quiz_details()


@register.simple_tag
def current_unit(course, student):
    return course.get_current_unit(student)


@register.simple_tag
def module_completion_percent(course, module, user):
    return module.get_module_complete_percent(course, user)


@register.simple_tag
def course_completion_percent(course, user):
    return course.percent_completed(user)
