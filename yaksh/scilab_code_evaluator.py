#!/usr/bin/env python
from __future__ import unicode_literals
import traceback
import os
from os.path import join, isfile
import subprocess
import re
import importlib

# Local imports
from .code_evaluator import CodeEvaluator
from .file_utils import copy_files, delete_files


class ScilabCodeEvaluator(CodeEvaluator):
    """Tests the Scilab code obtained from Code Server"""
    def setup(self):
        super(ScilabCodeEvaluator, self).setup()
        self.files = []
        self.submit_code_path = \
            self.create_submit_code_file('function.sci')

    def teardown(self):
        # Delete the created file.
        os.remove(self.submit_code_path)
        if self.files:
            delete_files(self.files)
        super(ScilabCodeEvaluator, self).teardown()

    def check_code(self, user_answer, file_paths, partial_grading, test_case, marks):
        if file_paths:
            self.files = copy_files(file_paths)
        ref_code_path = test_case
        clean_ref_path, clean_test_case_path = \
            self._set_test_code_file_path(ref_code_path)
        user_answer, terminate_commands = \
            self._remove_scilab_exit(user_answer.lstrip())

        success = False
        test_case_marks = 0.0

        self.write_to_submit_code_file(self.submit_code_path, user_answer)
        # Throw message if there are commmands that terminates scilab
        add_err = ""
        if terminate_commands:
            add_err = "Please do not use exit, quit and abort commands in your\
                        code.\n Otherwise your code will not be evaluated\
                        correctly.\n"

        cmd = 'printf "lines(0)\nexec(\'{0}\',2);\nquit();"'.format(
            clean_ref_path
        )
        cmd += ' | timeout 8 scilab-cli -nb'
        ret = self._run_command(cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        proc, stdout, stderr = ret 

        # Get only the error.
        stderr = self._get_error(stdout)
        if stderr is None:
            # Clean output
            stdout = self._strip_output(stdout)
            if proc.returncode == 5:
                success, err = True, "Correct answer"
                test_case_marks = float(marks) if partial_grading else 0.0
            else:
                err = add_err + stdout
        else:
            err = add_err + stderr
        return success, err, test_case_marks

    def _remove_scilab_exit(self, string):
        """
            Removes exit, quit and abort from the scilab code
        """
        new_string = ""
        terminate_commands = False
        for line in string.splitlines():
            new_line = re.sub(r"exit.*$", "", line)
            new_line = re.sub(r"quit.*$", "", new_line)
            new_line = re.sub(r"abort.*$", "", new_line)
            if line != new_line:
                terminate_commands = True
            new_string = new_string + '\n' + new_line
        return new_string, terminate_commands

    def _get_error(self, string):
        """
            Fetches only the error from the string.
            Returns None if no error.
        """
        obj = re.search("!.+\n.+", string)
        if obj:
            return obj.group()
        return None

    def _strip_output(self, out):
        """
            Cleans whitespace from the output
        """
        strip_out = "Message"
        for l in out.split('\n'):
            if l.strip():
                strip_out = strip_out+"\n"+l.strip()
        return strip_out

