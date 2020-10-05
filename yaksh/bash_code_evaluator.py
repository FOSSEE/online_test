#!/usr/bin/env python
from __future__ import unicode_literals
import os
from os.path import isfile
import subprocess

# local imports
from .base_evaluator import BaseEvaluator
from .file_utils import copy_files, delete_files


class BashCodeEvaluator(BaseEvaluator):
    # Private Protocol ##########
    def __init__(self, metadata, test_case_data):
        self.files = []
        self.submit_code_path = ""
        self.test_code_path = ""
        self.tc_args_path = ""

        # Set metadata values
        self.user_answer = metadata.get('user_answer')
        self.file_paths = metadata.get('file_paths')
        self.partial_grading = metadata.get('partial_grading')

        # Set test case data values
        self.test_case = test_case_data.get('test_case')
        self.test_case_args = test_case_data.get('test_case_args')

        self.weight = test_case_data.get('weight')
        self.hidden = test_case_data.get('hidden')

    def teardown(self):
        # Delete the created file.
        if os.path.exists(self.submit_code_path):
            os.remove(self.submit_code_path)
        if os.path.exists(self.test_code_path):
            os.remove(self.test_code_path)
        if os.path.exists(self.tc_args_path):
            os.remove(self.tc_args_path)
        if self.files:
            delete_files(self.files)

    def check_code(self):
        """ Function validates student script using instructor script as
        reference. Test cases can optionally be provided.  The first argument
        ref_path, is the path to instructor script, it is assumed to
        have executable permission.  The second argument submit_path, is
        the path to the student script, it is assumed to have executable
        permission.  The Third optional argument is the path to test the
        scripts.  Each line in this file is a test case and each test case is
        passed to the script as standard arguments.

        Returns
        --------
        success - Boolean, indicating if code was executed successfully,
        correctly
        weight - Float, indicating total weight of all successful test cases
        error - String, error message if success is false

        returns (True, "Correct answer", 1.0) : If the student script passes
        all test cases/have same output, when compared to the instructor script

        returns (False, error_msg, 0.0): If the student script fails a single
        test/have dissimilar output, when compared to the instructor script.

        Returns (False, error_msg, 0.0): If mandatory arguments are not files
        or if the required permissions are not given to the file(s).
        """
        mark_fraction = 0.0
        self.submit_code_path = self.create_submit_code_file('submit.sh')
        self._set_file_as_executable(self.submit_code_path)
        self.test_code_path = self.create_submit_code_file('main.sh')
        self._set_file_as_executable(self.test_code_path)
        if self.test_case_args:
            self.tc_args_path = self.create_submit_code_file('main.args')
            self.write_to_submit_code_file(self.tc_args_path,
                                           self.test_case_args)
        shebang = "#!/bin/bash\n"
        self.user_answer = shebang + self.user_answer.replace("\r", "")
        self.test_case = self.test_case.replace("\r", "")
        self.write_to_submit_code_file(self.submit_code_path, self.user_answer)
        self.write_to_submit_code_file(self.test_code_path, self.test_case)
        clean_ref_code_path, clean_test_case_path = \
            self.test_code_path, self.tc_args_path

        if self.file_paths:
            self.files = copy_files(self.file_paths)
        if not isfile(clean_ref_code_path):
            msg = "No file at %s or Incorrect path" % clean_ref_code_path
            return False, msg, 0.0
        if not isfile(self.submit_code_path):
            msg = "No file at %s or Incorrect path" % self.submit_code_path
            return False, msg, 0.0
        if not os.access(clean_ref_code_path, os.X_OK):
            msg = "Script %s is not executable" % clean_ref_code_path
            return False, msg, 0.0
        if not os.access(self.submit_code_path, os.X_OK):
            msg = "Script %s is not executable" % self.submit_code_path
            return False, msg, 0.0

        if not clean_test_case_path:
            ret = self._run_command(["bash", clean_ref_code_path],
                                    stdin=None,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
            proc, inst_stdout, inst_stderr = ret
            ret = self._run_command(["bash", self.submit_code_path],
                                    stdin=None,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
            proc, stdnt_stdout, stdnt_stderr = ret
            if inst_stdout == stdnt_stdout:
                mark_fraction = 1.0 if self.partial_grading else 0.0
                return True, None, mark_fraction
            else:
                err = "Error: expected %s, got %s" % (
                    inst_stdout + inst_stderr,
                    stdnt_stdout + stdnt_stderr
                )
                return False, err, 0.0
        else:
            if not isfile(clean_test_case_path):
                msg = "No test case at %s" % clean_test_case_path
                return False, msg, 0.0
            if not os.access(clean_ref_code_path, os.R_OK):
                msg = "Test script %s, not readable" % clean_test_case_path
                return False, msg, 0.0
            # valid_answer is True, so that we can stop once a test case fails
            valid_answer = True
            # loop_count has to be greater than or equal to one.
            # Useful for caching things like empty test files,etc.
            loop_count = 0
            test_cases = open(clean_test_case_path).readlines()
            num_lines = len(test_cases)
            for tc in test_cases:
                loop_count += 1
                if valid_answer:
                    args = ["bash", clean_ref_code_path] + \
                        [x for x in tc.split()]
                    ret = self._run_command(args,
                                            stdin=None,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE
                                            )
                    proc, inst_stdout, inst_stderr = ret
                    if self.file_paths:
                        self.files = copy_files(self.file_paths)
                    args = ["bash", self.submit_code_path] + \
                        [x for x in tc.split()]
                    ret = self._run_command(args,
                                            stdin=None,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE
                                            )
                    proc, stdnt_stdout, stdnt_stderr = ret
                    valid_answer = inst_stdout == stdnt_stdout
            if valid_answer and (num_lines == loop_count):
                mark_fraction = 1.0 if self.partial_grading else 0.0
                return True, None, mark_fraction
            else:
                err = ("Error:expected {0}, got {1}").format(
                        inst_stdout+inst_stderr,
                        stdnt_stdout+stdnt_stderr
                    )
                return False, err, 0.0
