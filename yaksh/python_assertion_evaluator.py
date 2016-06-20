#!/usr/bin/env python
import sys
import traceback
import os
from os.path import join
import importlib

# local imports
from code_evaluator import CodeEvaluator, TimeoutException
from copy_delete_files import CopyDeleteFiles


class PythonAssertionEvaluator(CodeEvaluator):
    """Tests the Python code obtained from Code Server"""

    def setup(self):
        super(PythonAssertionEvaluator, self).setup()
        self.exec_scope = None

    def teardown(self):
        super(PythonAssertionEvaluator, self).teardown()
        # Delete the created file.
        if self.files_list:
            file_delete = CopyDeleteFiles()
            file_delete.delete_files(self.files_list)

    def compile_code(self, user_answer, file_paths, test_case):
        self.files_list = []
        if file_paths:
            file_copy = CopyDeleteFiles()
            self.files_list = file_copy.copy_files(file_paths)
        if self.exec_scope:
            return None
        else:
            submitted = compile(user_answer, '<string>', mode='exec')
            self.exec_scope = {}
            exec submitted in self.exec_scope
            return self.exec_scope

    def check_code(self, user_answer, file_paths, test_case):
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
        except TimeoutException:
            raise
        else:
            success = True
            err = 'Correct answer'
        del tb
        return success, err
