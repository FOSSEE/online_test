#!/usr/bin/env python
import sys
import traceback
import os
import re
from os.path import join
import importlib

# Local imports
from .file_utils import copy_files, delete_files
from .base_evaluator import BaseEvaluator
from .grader import TimeoutException


class PythonAssertionEvaluator(BaseEvaluator):
    """Tests the Python code obtained from Code Server"""

    def __init__(self, metadata, test_case_data):
        self.exec_scope = None
        self.files = []

        # Set metadata values
        self.user_answer = metadata.get('user_answer')
        self.file_paths = metadata.get('file_paths')
        self.partial_grading = metadata.get('partial_grading')

        # Set test case data values
        self.test_case = test_case_data.get('test_case')
        self.weight = test_case_data.get('weight')

    def teardown(self):
        # Delete the created file.
        if self.files:
            delete_files(self.files)

    def compile_code(self):
        if self.file_paths:
            self.files = copy_files(self.file_paths)
        if self.exec_scope:
            return None
        else:
            submitted = compile(self.user_answer, '<string>', mode='exec')
            self.exec_scope = {}
            exec(submitted, self.exec_scope)
            return self.exec_scope

    def check_code(self):
        """ Function validates user answer by running an assertion based test case
        against it

        Returns
        --------
        Returns a tuple (success, error, test_case_weight)

        success - Boolean, indicating if code was executed successfully, correctly
        weight - Float, indicating total weight of all successful test cases
        error - String, error message if success is false

        returns (True, "Correct answer", 1.0) : If the student script passes all
        test cases/have same output, when compared to the instructor script

        returns (False, error_msg, 0.0): If the student script fails a single
        test/have dissimilar output, when compared to the instructor script.

        Returns (False, error_msg, 0.0): If mandatory arguments are not files or if
        the required permissions are not given to the file(s).
        """
        success = False
        mark_fraction = 0.0
        try:
            tb = None
            _tests = compile(self.test_case, '<string>', mode='exec')
            exec(_tests, self.exec_scope)
        except TimeoutException:
            raise
        except Exception:
            type, value, tb = sys.exc_info()
            info = traceback.extract_tb(tb)
            fname, lineno, func, text = info[-1]
            text = str(self.test_case)

            # Get truncated traceback
            err_tb_lines = traceback.format_exc().splitlines()
            stripped_tb_lines = []
            for line in err_tb_lines:
                line = re.sub(r'File\s+".*?",\s+line',
                     'File <file>, line',
                     line
                    )
                stripped_tb_lines.append(line)
            stripped_tb = '\n'.join(stripped_tb_lines[-10::])

            err = "Expected Test Case:\n{0}\n" \
                "Error Traceback - {1} {2} in:\n {3}\n{4}".format(
                    self.test_case,
                    type.__name__,
                    str(value),
                    text,
                    stripped_tb
                    )
        else:
            success = True
            err = None
            mark_fraction = 1.0 if self.partial_grading else 0.0
        del tb
        return success, err, mark_fraction
