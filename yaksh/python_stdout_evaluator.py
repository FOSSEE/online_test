#!/usr/bin/env python
import sys
import traceback
import os
from os.path import join
import importlib
from contextlib import contextmanager

# local imports
from code_evaluator import CodeEvaluator


@contextmanager
def redirect_stdout():
    from StringIO import StringIO
    new_target = StringIO()

    old_target, sys.stdout = sys.stdout, new_target # replace sys.stdout
    try:
        yield new_target # run some code with the replaced stdout
    finally:
        sys.stdout = old_target # restore to the previous value


class PythonStdoutEvaluator(CodeEvaluator):
    """Tests the Python code obtained from Code Server"""

    def check_code(self, user_answer, test_cases):
        success = False

        tb = None
        expected_output = test_cases[0]
        submitted = compile(user_answer, '<string>', mode='exec')
        with redirect_stdout() as output_buffer:
            g = {}
            exec submitted in g
        raw_output_value = output_buffer.getvalue()
        output_value = raw_output_value.encode('string_escape').strip()
        if output_value == str(test_code):
            success = True
            err = 'Correct answer'
        else:
            success = False
            err = "Incorrect Answer"

        del tb
        return success, err

    # def unpack_test_case_data(self, test_case_data):
    #     for t in test_case_data:
    #         test_case = t.get('output')

    #     return test_case
