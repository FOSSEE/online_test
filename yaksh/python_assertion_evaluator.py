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

    def setup(self):
        super(PythonAssertionEvaluator, self).setup()
        self.exec_scope = None

    def compile_code(self, user_answer, test_case):
        if self.exec_scope:
            return None
        else:
            submitted = compile(user_answer, '<string>', mode='exec')
            self.exec_scope = {}
            exec submitted in self.exec_scope
            return self.exec_scope

    def check_code(self, user_answer, test_case):
        success = False
        try:
            tb = None
            _tests = compile(test_case, '<string>', mode='exec')
            exec _tests in self.exec_scope
        except AssertionError:
            type, value, tb = sys.exc_info()
            info = traceback.extract_tb(tb)
            fname, lineno, func, text = info[-1]
            text = str(test_case).splitlines()[lineno-1]
            err = "{0} {1} in: {2}".format(type.__name__, str(value), text)
        else:
            success = True
            err = 'Correct answer'

        del tb
        return success, err
