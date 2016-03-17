#!/usr/bin/env python
import sys
import traceback
import os
from os.path import join
import importlib

# local imports
from code_evaluator import CodeEvaluator


class PythonAssertionEvaluator(CodeEvaluator):
    """Tests the Python code obtained from Code Server"""

    # def check_code(self, test, user_answer, ref_code_path):
    def check_code(self, user_answer, test_case_data):
        success = False
        try:
            tb = None
            submitted = compile(user_answer, '<string>', mode='exec')
            g = {}
            exec submitted in g
            for test_code in test_case_data:
                _tests = compile(test_code, '<string>', mode='exec')
                exec _tests in g
        except AssertionError:
            type, value, tb = sys.exc_info()
            info = traceback.extract_tb(tb)
            fname, lineno, func, text = info[-1]
            text = str(test_code).splitlines()[lineno-1]
            err = "{0} {1} in: {2}".format(type.__name__, str(value), text)
        else:
            success = True
            err = 'Correct answer'

        del tb
        return success, err
