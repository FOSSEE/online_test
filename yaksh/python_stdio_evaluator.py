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
from file_utils import copy_files, delete_files
from textwrap import dedent
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

    def teardown(self):
        super(PythonStdioEvaluator, self).teardown()
        # Delete the created file.
        if self.files:
            delete_files(self.files)


    def compile_code(self, user_answer, file_paths, expected_input, expected_output):
        self.files = []
        if file_paths:
            self.files = copy_files(file_paths)
        submitted = compile(user_answer, '<string>', mode='exec')
        if expected_input:
            input_buffer = StringIO()
            input_buffer.write(expected_input)
            input_buffer.seek(0)
            sys.stdin = input_buffer
        with redirect_stdout() as output_buffer:
            exec_scope = {}
            exec submitted in exec_scope
        self.output_value = output_buffer.getvalue().rstrip("\n")
        return self.output_value

    def check_code(self, user_answer, file_paths, expected_input, expected_output):
        success = False

        tb = None
        if self.output_value == expected_output:
            success = True
            err = "Correct Answer"
        else:
            success = False
            err = dedent("""
                Incorrect Answer:
                Given input - {0}
                Expected output - {1}
                Your output - {2}
                """
                         .format(expected_input,
                                 expected_output, self.output_value
                                 )
                         )
        del tb
        return success, err
