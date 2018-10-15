from django import template
from django.template.defaultfilters import stringfilter
from ast import literal_eval
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
def module_completion_percent(course, module, user):
    return module.get_module_complete_percent(course, user)


@register.simple_tag
def course_completion_percent(course, user):
    return course.percent_completed(user)


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
def get_questions_by_type(all_questions, question_type):
    return [question for question in all_questions if question.type == question_type]


@register.simple_tag
def course_grade(course, user):
    return course.get_grade(user)
