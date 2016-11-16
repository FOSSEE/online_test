#!/usr/bin/env python
from __future__ import unicode_literals
import sys
import traceback
import os
from os.path import join
import importlib

# Local imports
from .code_evaluator import CodeEvaluator, TimeoutException
from .file_utils import copy_files, delete_files


class PythonAssertionEvaluator(CodeEvaluator):
    """Tests the Python code obtained from Code Server"""

    def setup(self):
        super(PythonAssertionEvaluator, self).setup()
        self.exec_scope = None
        self.files = []

    def teardown(self):
        # Delete the created file.
        if self.files:
            delete_files(self.files)
        super(PythonAssertionEvaluator, self).teardown()

    def compile_code(self, user_answer, file_paths, test_case, weight):
        if file_paths:
            self.files = copy_files(file_paths)
        if self.exec_scope:
            return None
        else:
            submitted = compile(user_answer, '<string>', mode='exec')
            self.exec_scope = {}
            exec(submitted, self.exec_scope)
            return self.exec_scope

    def check_code(self, user_answer, file_paths, partial_grading, test_case, weight):
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
        test_case_weight = 0.0
        try:
            tb = None
            _tests = compile(test_case, '<string>', mode='exec')
            exec(_tests, self.exec_scope)
        except AssertionError:
            type, value, tb = sys.exc_info()
            info = traceback.extract_tb(tb)
            fname, lineno, func, text = info[-1]
            text = str(test_case).splitlines()[lineno-1]
            err = "{0} {1} in: {2}".format(type.__name__, str(value), text)
        except Exception:
            raise  # Exception will be caught in CodeEvaluator.
        else:
            success = True
            err = 'Correct answer'
            test_case_weight = float(weight) if partial_grading else 0.0
        del tb
        return success, err, test_case_weight
