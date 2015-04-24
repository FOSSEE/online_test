#!/usr/bin/env python
import traceback
import pwd
import os
from os.path import join, isfile
import subprocess
import importlib

# local imports
from evaluate_code import EvaluateCode
from language_registry import registry


class EvaluateBashCode(EvaluateCode):
    """Tests the Bash code obtained from Code Server"""
    ## Public Protocol ##########
    def evaluate_code(self):
        submit_path = self.create_submit_code_file('submit.sh')
        self.set_file_as_executable(submit_path)
        get_ref_path, get_test_case_path = self.ref_code_path.strip().split(',')
        get_ref_path = get_ref_path.strip()
        get_test_case_path = get_test_case_path.strip()
        ref_path, test_case_path = self.set_test_code_file_path(get_ref_path, get_test_case_path)

        success, err = self._check_bash_script(ref_path, submit_path,
                            test_case_path)

        # Delete the created file.
        os.remove(submit_path)

        return success, err

    ## Private Protocol ##########
    def _check_bash_script(self, ref_path, submit_path,
                          test_case_path=None):
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
        if not isfile(ref_path):
            return False, "No file at %s or Incorrect path" % ref_path
        if not isfile(submit_path):
            return False, "No file at %s or Incorrect path" % submit_path
        if not os.access(ref_path, os.X_OK):
            return False, "Script %s is not executable" % ref_path
        if not os.access(submit_path, os.X_OK):
            return False, "Script %s is not executable" % submit_path

        success = False

        if test_case_path is None or "":
            ret = self.run_command(ref_path, stdin=None,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc, inst_stdout, inst_stderr = ret
            ret = self.run_command(submit_path, stdin=None,
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
            if not isfile(test_case_path):
                return False, "No test case at %s" % test_case_path
            if not os.access(ref_path, os.R_OK):
                return False, "Test script %s, not readable" % test_case_path
            valid_answer = True  # We initially make it one, so that we can
                                 # stop once a test case fails
            loop_count = 0  # Loop count has to be greater than or
                            # equal to one.
                            # Useful for caching things like empty
                            # test files,etc.
            test_cases = open(test_case_path).readlines()
            num_lines = len(test_cases)
            for test_case in test_cases:
                loop_count += 1
                if valid_answer:
                    args = [ref_path] + [x for x in test_case.split()]
                    ret = self.run_command(args, stdin=None,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                    proc, inst_stdout, inst_stderr = ret
                    args = [submit_path]+[x for x in test_case.split()]
                    ret = self.run_command(args, stdin=None,
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


registry.register('bash', EvaluateBashCode)