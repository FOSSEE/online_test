#!/usr/bin/env python
from __future__ import unicode_literals
import os
from os.path import isfile
import subprocess

# Local imports
from .file_utils import copy_files, delete_files
from .base_evaluator import BaseEvaluator
from .grader import CompilationError, TestCaseError
from .error_messages import prettify_exceptions


class CppCodeEvaluator(BaseEvaluator):
    """Tests the C code obtained from Code Server"""
    def __init__(self, metadata, test_case_data):
        self.files = []
        self.compiled_user_answer = None
        self.compiled_test_code = None
        self.user_output_path = ""
        self.ref_output_path = ""
        self.submit_code_path = ""
        self.test_code_path = ""

        # Set metadata values
        self.user_answer = metadata.get('user_answer')
        self.file_paths = metadata.get('file_paths')
        self.partial_grading = metadata.get('partial_grading')

        # Set test case data values
        self.test_case = test_case_data.get('test_case')
        self.weight = test_case_data.get('weight')
        self.hidden = test_case_data.get('hidden')

    def teardown(self):
        # Delete the created file.
        if os.path.exists(self.submit_code_path):
            os.remove(self.submit_code_path)
        if os.path.exists(self.ref_output_path):
            os.remove(self.ref_output_path)
        if os.path.exists(self.user_output_path):
            os.remove(self.user_output_path)
        if os.path.exists(self.test_code_path):
            os.remove(self.test_code_path)
        if self.files:
            delete_files(self.files)

    def set_file_paths(self):
        user_output_path = os.getcwd() + '/output_file'
        ref_output_path = os.getcwd() + '/executable'

        return user_output_path, ref_output_path

    def get_commands(self, clean_ref_code_path, user_output_path,
                     ref_output_path):
        compile_command = 'g++  {0} -c -o {1}'.format(
            self.submit_code_path, user_output_path)
        compile_main = 'g++ {0} {1} -o {2}'.format(
            clean_ref_code_path, user_output_path,
            ref_output_path
            )
        return compile_command, compile_main

    def compile_code(self):
        if self.compiled_user_answer and self.compiled_test_code:
            return None
        else:
            self.submit_code_path = self.create_submit_code_file('submit.c')
            self.test_code_path = self.create_submit_code_file('main.c')
            self.write_to_submit_code_file(self.submit_code_path,
                                           self.user_answer)
            self.write_to_submit_code_file(self.test_code_path, self.test_case)
            clean_ref_code_path = self.test_code_path
            if self.file_paths:
                self.files = copy_files(self.file_paths)
            if not isfile(clean_ref_code_path):
                msg = "No file at %s or Incorrect path" % clean_ref_code_path
                return False, msg
            if not isfile(self.submit_code_path):
                msg = "No file at %s or Incorrect path" % self.submit_code_path
                return False, msg

            self.user_output_path, self.ref_output_path = self.set_file_paths()
            self.compile_command, self.compile_main = self.get_commands(
                clean_ref_code_path,
                self.user_output_path,
                self.ref_output_path
            )
            self.compiled_user_answer = self._run_command(
                self.compile_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.compiled_test_code = self._run_command(
                self.compile_main,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            return self.compiled_user_answer, self.compiled_test_code

    def check_code(self):
        """ Function validates student code using instructor code as
        reference.The first argument ref_code_path, is the path to
        instructor code, it is assumed to have executable permission.
        The second argument submit_code_path, is the path to the student
        code, it is assumed to have executable permission.

        Returns
        --------

        returns (True, "Correct answer") : If the student function returns
        expected output when called by reference code.

        returns (False, error_msg): If the student function fails to return
        expected output when called by reference code.

        Returns (False, error_msg): If mandatory arguments are not files or
        if the required permissions are not given to the file(s).
        """
        success = False
        mark_fraction = 0.0

        proc, stdnt_out, stdnt_stderr = self.compiled_user_answer
        stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)

        # Only if compilation is successful, the program is executed
        # And tested with testcases
        if stdnt_stderr == '':
            proc, main_out, main_err = self.compiled_test_code
            main_err = self._remove_null_substitute_char(main_err)
            if main_err == '':
                ret = self._run_command([self.ref_output_path],
                                        stdin=None,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE
                                        )
                proc, stdout, stderr = ret
                if proc.returncode == 0:
                    success, err = True, None
                    mark_fraction = 1.0 if self.partial_grading else 0.0
                else:
                    err = "{0} \n {1}".format(stdout, stderr)
                    err = prettify_exceptions('AssertionError', err)
                    return success, err, mark_fraction
            else:
                err = "Test case Error:"
                try:
                    error_lines = main_err.splitlines()
                    for e in error_lines:
                        if ':' in e:
                            err = "{0} \n {1}".format(err, e.split(":", 1)[1])
                        else:
                            err = "{0} \n {1}".format(err, e)
                except Exception:
                        err = "{0} \n {1}".format(err, main_err)
                raise TestCaseError(err)
        else:
            err = "Compilation Error:"
            try:
                error_lines = stdnt_stderr.splitlines()
                for e in error_lines:
                    if ':' in e:
                        err = "{0} \n {1}".format(err, e.split(":", 1)[1])
                    else:
                        err = "{0} \n {1}".format(err, e)
            except Exception:
                err = "{0} \n {1}".format(err, stdnt_stderr)
            raise CompilationError(err)

        return success, err, mark_fraction
