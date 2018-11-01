#!/usr/bin/env python
from __future__ import unicode_literals
import traceback
import pwd
import os
from os.path import join, isfile
import subprocess

# Local imports
from .file_utils import copy_files, delete_files
from .base_evaluator import BaseEvaluator


class rubyCodeEvaluator(BaseEvaluator):
    """Tests the ruby code obtained from Code Server"""
    def __init__(self, metadata, test_case_data):
        self.files = []
        self.process = None
        self.submit_code_path = ""

        # Set metadata values
        self.user_answer = metadata.get('user_answer')
        self.file_paths = metadata.get('file_paths')
        self.partial_grading = metadata.get('partial_grading')

        # Set test case data values
        self.test_case = test_case_data.get('test_case')
        self.weight = test_case_data.get('weight')

    def teardown(self):
        # Delete the created file.
        if os.path.exists(self.submit_code_path):
            os.remove(self.submit_code_path)
        if self.files:
            delete_files(self.files)

    def compile_code(self):
        self.submit_code_path = self.create_submit_code_file('submit.rb')
        submit_f = open(self.submit_code_path, 'w')
        submit_f.write(self.user_answer.lstrip())
        submit_f.write('\n')
        submit_f.write(self.test_case.lstrip())
        submit_f.close()
        self.process = self._run_command(
                'ruby {0}'.format(self.submit_code_path),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

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
        proc, stdnt_out, stdnt_stderr = self.process
        stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)
        if stdnt_stderr == '':
            if proc.returncode == 0:
                success, err = True, None
                mark_fraction = 1.0 if self.partial_grading else 0.0
            else:
                err = "{0} \n {1}".format(stdout, stderr)
        else:
            err = "Error:"
            try:
                error_lines = stdnt_stderr.splitlines()
                for e in error_lines:
                    if ':' in e:
                        err = "{0} \n {1}".format(err, e.split(":", 1)[1])
                    else:
                        err = "{0} \n {1}".format(err, e)
            except:
                err = "{0} \n {1}".format(err, stdnt_stderr)
        return success, err, mark_fraction
