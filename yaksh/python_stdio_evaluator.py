#!/usr/bin/env python
import sys
import traceback
import os
from os.path import join
import importlib
from contextlib import contextmanager
from ast import literal_eval
# local imports
from code_evaluator import CodeEvaluator
from StringIO import StringIO


@contextmanager
def redirect_stdout():
    new_target = StringIO()

    old_target, sys.stdout = sys.stdout, new_target  # replace sys.stdout
    try:
        yield new_target  # run some code with the replaced stdout
    finally:
        sys.stdout = old_target  # restore to the previous value


class PythonStdioEvaluator(CodeEvaluator):
    """Tests the Python code obtained from Code Server"""

    def compile_code(self, user_answer, expected_input, expected_output):
        submitted = compile(user_answer, '<string>', mode='exec')
        if expected_input:
            input_buffer = StringIO()
            try:
                literal_input = literal_eval(expected_input.split("\n"))
            except ValueError:
                literal_input = expected_input.split("\n")
            for inputs in literal_input:
                input_buffer.write(str(inputs)+'\n')
            input_buffer.seek(0)
            sys.stdin = input_buffer

        with redirect_stdout() as output_buffer:
            exec_scope = {}
            exec submitted in exec_scope
        self.output_value = output_buffer.getvalue().rstrip("\n")
        return self.output_value

    def check_code(self, user_answer, expected_input, expected_output):
        success = False

        tb = None
        if expected_output in user_answer:
            success = False
            err = ("Incorrect Answer: Please avoid "
                   "printing the expected output directly"
                   )
        elif self.output_value == expected_output:

            success = True
            err = "Correct Answer"

        else:
            success = False
            err = """Incorrect Answer:\nExpected output - {0}
                     and your output - {1}"""\
                  .format(expected_output, self.output_value)

        del tb
        return success, err
