#!/usr/bin/env python
from __future__ import unicode_literals
import os
import subprocess
import re

# Local imports
from .base_evaluator import BaseEvaluator
from .file_utils import copy_files, delete_files


class ScilabCodeEvaluator(BaseEvaluator):
    """Tests the Scilab code obtained from Code Server"""
    def __init__(self, metadata, test_case_data):
        self.files = []
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
        if os.path.exists(self.test_code_path):
            os.remove(self.test_code_path)
        if self.files:
            delete_files(self.files)

    def check_code(self):
        self.submit_code_path = self.create_submit_code_file('function.sci')
        self.test_code_path = self.create_submit_code_file('main.sci')
        if self.file_paths:
            self.files = copy_files(self.file_paths)
        clean_ref_path = self.test_code_path
        self.user_answer, terminate_commands = \
            self._remove_scilab_exit(self.user_answer.lstrip())

        success = False
        mark_fraction = 0.0
        self.write_to_submit_code_file(self.submit_code_path, self.user_answer)
        self.write_to_submit_code_file(self.test_code_path, self.test_case)
        # Throw message if there are commmands that terminates scilab
        add_err = ""
        if terminate_commands:
            add_err = "Please do not use exit, quit and abort commands in your\
                        code.\n Otherwise your code will not be evaluated\
                        correctly.\n"

        cmd = 'printf "lines(0)\nexec(\'{0}\',2);\nquit();"'.format(
            clean_ref_path
        )
        cmd += ' | scilab-cli -nb'
        ret = self._run_command(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )
        proc, stdout, stderr = ret

        # Get only the error.
        stderr = self._get_error(stdout)
        if stderr is None:
            # Clean output
            stdout = self._strip_output(stdout)
            if proc.returncode == 5:
                success, err = True, None
                mark_fraction = 1.0 if self.partial_grading else 0.0
            else:
                err = add_err + stdout
        else:
            err = add_err + stderr

        return success, err, mark_fraction

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
