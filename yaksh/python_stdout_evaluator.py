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

    def compile_code(self, user_answer, expected_output):
        if hasattr(self, 'output_value'):
            return None
        else:
            submitted = compile(user_answer, '<string>', mode='exec')
            with redirect_stdout() as output_buffer:
                exec_scope = {}
                exec submitted in exec_scope
            self.output_value = output_buffer.getvalue()
            return self.output_value

    def check_code(self, user_answer, expected_output):
        success = False

        tb = None
        if expected_output in user_answer:
            success = False
            err = ("Incorrect Answer: Please avoid "
                "printing the expected output directly"
            )
        elif self.output_value == expected_output:
            success = True
            err = "Correct answer"

        else:
            success = False
            err = "Incorrect Answer"

        del tb
        return success, err

