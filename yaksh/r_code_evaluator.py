#!/usr/bin/env python
from __future__ import unicode_literals
import os
import subprocess
import re

# Local imports
from .base_evaluator import BaseEvaluator
from .file_utils import copy_files, delete_files
from .error_messages import prettify_exceptions


class RCodeEvaluator(BaseEvaluator):
    """Tests the R code obtained from Code Server"""
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
        self.submit_code_path = self.create_submit_code_file('function.r')
        self.test_code_path = self.create_submit_code_file('main.r')
        if self.file_paths:
            self.files = copy_files(self.file_paths)
        clean_ref_path = self.test_code_path
        self.user_answer, terminate_commands = \
            self._remove_r_quit(self.user_answer.lstrip())

        success = False
        mark_fraction = 0.0
        self.write_to_submit_code_file(self.submit_code_path, self.user_answer)
        self.write_to_submit_code_file(self.test_code_path, self.test_case)
        # Throw message if there are commmands that terminates scilab
        add_err = ""
        if terminate_commands:
            add_err = "Please do not use quit() q() in your code.\
                        \n Otherwise your code will not be evaluated.\n"

        cmd = 'Rscript main.r'
        ret = self._run_command(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )
        proc, stdout, stderr = ret

        if stderr is '':
            # Clean output
            stdout = self._strip_output(stdout)
            if proc.returncode == 31:
                success, err = True, None
                mark_fraction = 1.0 if self.partial_grading else 0.0
            else:
                err = stdout + add_err
        else:
            err = stderr + add_err
        if err:
            err = re.sub(r'.*?: ', '', err, count=1)
            err = prettify_exceptions('Error', err)
        return success, err, mark_fraction

    def _remove_r_quit(self, string):
        """
            Removes quit from the R code
        """
        new_string = ""
        terminate_commands = False
        for line in string.splitlines():
            new_line = re.sub(r'quit(.*$)', "", line)
            new_line = re.sub(r'q(.*$)', "", new_line)
            if line != new_line:
                terminate_commands = True
            new_string = new_string + '\n' + new_line
        return new_string, terminate_commands

    def _strip_output(self, out):
        """
            Cleans whitespace from the output
        """
        strip_out = "Message"
        for l in out.split('\n'):
            if l.strip():
                strip_out = strip_out+"\n"+l.strip()
        return strip_out + out
