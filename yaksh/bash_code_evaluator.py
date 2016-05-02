#!/usr/bin/env python
import traceback
import pwd
import os
from os.path import join, isfile
import sys
import subprocess
import importlib

# local imports
from code_evaluator import CodeEvaluator


class BashCodeEvaluator(CodeEvaluator):
    # Private Protocol ##########
    def setup(self):
        super(BashCodeEvaluator, self).setup()
        self.submit_code_path = self.create_submit_code_file('submit.sh')
        self._set_file_as_executable(self.submit_code_path)

    def teardown(self):
        # Delete the created file.
        super(BashCodeEvaluator, self).teardown()
        os.remove(self.submit_code_path)

    def check_code(self, user_answer, test_case):
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

        returns (True, "Correct answer") : If the student script passes all
        test cases/have same output, when compared to the instructor script

        returns (False, error_msg): If the student script fails a single
        test/have dissimilar output, when compared to the instructor script.

        Returns (False, error_msg): If mandatory arguments are not files or if
        the required permissions are not given to the file(s).

        """
        ref_code_path = test_case
        get_ref_path, get_test_case_path = ref_code_path.strip().split(',')
        get_ref_path = get_ref_path.strip()
        get_test_case_path = get_test_case_path.strip()
        clean_ref_code_path, clean_test_case_path = self._set_test_code_file_path(get_ref_path,
                                                             get_test_case_path)

        if not isfile(clean_ref_code_path):
            return False, "No file at %s or Incorrect path" % clean_ref_code_path
        if not isfile(self.submit_code_path):
            return False, "No file at %s or Incorrect path" % self.submit_code_path
        if not os.access(clean_ref_code_path, os.X_OK):
            return False, "Script %s is not executable" % clean_ref_code_path
        if not os.access(self.submit_code_path, os.X_OK):
            return False, "Script %s is not executable" % self.submit_code_path

        success = False
        self.write_to_submit_code_file(self.submit_code_path, user_answer)

        if clean_test_case_path is None or "":
            ret = self._run_command(clean_ref_code_path, stdin=None,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc, inst_stdout, inst_stderr = ret
            ret = self._run_command(self.submit_code_path, stdin=None,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc, stdnt_stdout, stdnt_stderr = ret
            if inst_stdout == stdnt_stdout:
                return True, "Correct answer"
            else:
                err = "Error: expected %s, got %s" % (inst_stderr,
                                                      stdnt_stderr)
                return False, err
        else:
            if not isfile(clean_test_case_path):
                return False, "No test case at %s" % clean_test_case_path
            if not os.access(clean_ref_code_path, os.R_OK):
                return False, "Test script %s, not readable" % clean_test_case_path
            # valid_answer is True, so that we can stop once a test case fails
            valid_answer = True
            # loop_count has to be greater than or equal to one.
            # Useful for caching things like empty test files,etc.
            loop_count = 0
            test_cases = open(clean_test_case_path).readlines()
            num_lines = len(test_cases)
            for test_case in test_cases:
                loop_count += 1
                if valid_answer:
                    args = [clean_ref_code_path] + [x for x in test_case.split()]
                    ret = self._run_command(args, stdin=None,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                    proc, inst_stdout, inst_stderr = ret
                    args = [self.submit_code_path]+[x for x in test_case.split()]
                    ret = self._run_command(args, stdin=None,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                    proc, stdnt_stdout, stdnt_stderr = ret
                    valid_answer = inst_stdout == stdnt_stdout
            if valid_answer and (num_lines == loop_count):
                return True, "Correct answer"
            else:
                err = "Error:expected %s, got %s" % (inst_stdout+inst_stderr,
                                                     stdnt_stdout+stdnt_stderr)
                return False, err
