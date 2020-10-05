from django import template
from django.template.defaultfilters import stringfilter
from django.forms.fields import CheckboxInput
from ast import literal_eval
import os
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from yaksh.models import User, Course, Quiz

register = template.Library()


@stringfilter
@register.filter(name='escape_quotes')
def escape_quotes(value):
    value = value.decode("utf-8")
    escape_single_quotes = value.replace("'", "\\'")
    escape_single_and_double_quotes = escape_single_quotes.replace('"', '\\"')

    return escape_single_and_double_quotes


@register.simple_tag(name="completed")
def completed(answerpaper):
    return answerpaper.filter(status="completed").count()


@register.simple_tag(name="inprogress")
def inprogress(answerpaper):
    return answerpaper.filter(status="inprogress").count()


@register.filter(name='zip')
def zip_longest_out(a, b):
    return zip_longest(a, b)

@register.filter(name='to_int')
def to_int(value):
    return int(value)

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
def module_completion_percent(course, module, user):
    return module.get_module_complete_percent(course, user)


@register.simple_tag
def get_ordered_testcases(question, answerpaper):
    return question.get_ordered_test_cases(answerpaper)


@register.simple_tag
def get_answer_for_arrange_options(ans, question):
    if type(ans) == bytes:
        ans = ans.decode("utf-8")
    else:
        ans = str(ans)
    answer = literal_eval(ans)
    testcases = []
    for answer_id in answer:
        tc = question.get_test_case(id=int(answer_id))
        testcases.append(tc)
    return testcases


@register.filter(name='replace_spaces')
def replace_spaces(name):
    return name.replace(" ", "_")


@register.simple_tag
def course_grade(course, user):
    return course.get_grade(user)


@register.filter(name='is_checkbox')
def is_checkbox(value):
    return isinstance(value, CheckboxInput)


@register.simple_tag
def pygmentise_user_answer(language, answer):
    lexer = get_lexer_by_name(language, stripall=True)
    formatter = HtmlFormatter(linenos="inline",
                              cssclass="highlight",
                              style="colorful")
    style = formatter.get_style_defs('.highlight')
    result = highlight(answer, lexer, formatter)
    return result, style


@register.simple_tag
def course_grade(course, user):
    return course.get_grade(user)


@register.filter(name='highlight_spaces')
def highlight_spaces(text):
    return text.replace(
        " ", '<span style="background-color:#ffb6db">&nbsp</span>'
        )


@register.filter(name="to_integer")
def to_integer(text):
    try:
        value = int(text)
    except ValueError:
        value = ''
    return value


@register.filter(name="to_float")
def to_float(text):
    try:
        value = float(text)
    except ValueError:
        value = ''
    return value


@register.filter(name="to_str")
def to_str(text):
    return text.decode("utf-8")


@register.inclusion_tag('yaksh/micromanaged.html')
def show_special_attempt(user_id, course_id):
    user = User.objects.get(pk=user_id)
    micromanagers = user.micromanaged.filter(course_id=course_id)
    context = {'micromanagers': micromanagers}
    return context


@register.inclusion_tag('yaksh/micromonitor.html')
def specail_attempt_monitor(user_id, course_id, quiz_id):
    user = User.objects.get(pk=user_id)
    micromanagers = user.micromanaged.filter(course_id=course_id,
                                             quiz_id=quiz_id)
    context = {'user_id': user_id, 'course_id': course_id, 'quiz_id': quiz_id}
    if micromanagers.exists():
        context['micromanager'] = micromanagers.first()
    return context
