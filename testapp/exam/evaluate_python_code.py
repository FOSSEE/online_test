#!/usr/bin/env python
import sys
import traceback
import os
from os.path import join
import importlib

# local imports
from evaluate_code import EvaluateCode
from language_registry import registry


class EvaluatePythonCode(EvaluateCode):
    """Tests the Python code obtained from Code Server"""
    # Public Protocol ##########
    def evaluate_code(self):
        success = False

        try:
            tb = None
            test_code = self._create_test_case()
            submitted = compile(self.user_answer, '<string>', mode='exec')
            g = {}
            exec submitted in g
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

    # Private Protocol ##########
    def _create_test_case(self):
        """
            Create assert based test cases in python
        """
        test_code = ""
        for test_case in self.test_case_data:
            pos_args = ", ".join(str(i) for i in test_case.get('pos_args')) \
                                if test_case.get('pos_args') else ""
            kw_args = ", ".join(str(k+"="+a) for k, a
                             in test_case.get('kw_args').iteritems()) \
                            if test_case.get('kw_args') else ""
            args = pos_args + ", " + kw_args if pos_args and kw_args \
                                                else pos_args or kw_args
            tcode = "assert {0}({1}) == {2}".format(test_case.get('func_name'),
                                                        args, test_case.get('expected_answer'))
            test_code += tcode + "\n"
        return test_code


registry.register('python', EvaluatePythonCode)
