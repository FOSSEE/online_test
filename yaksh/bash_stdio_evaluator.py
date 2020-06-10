#!/usr/bin/env python
from __future__ import unicode_literals
import subprocess
import os
from os.path import isfile

# local imports
from .stdio_evaluator import StdIOEvaluator
from .file_utils import copy_files, delete_files


class BashStdIOEvaluator(StdIOEvaluator):
    """Evaluates Bash StdIO based code"""
    def __init__(self, metadata, test_case_data):
        self.files = []

        # Set metadata values
        self.user_answer = metadata.get('user_answer')
        self.file_paths = metadata.get('file_paths')
        self.partial_grading = metadata.get('partial_grading')

        # Set test case data values
        self.expected_input = test_case_data.get('expected_input')
        self.expected_output = test_case_data.get('expected_output')
        self.weight = test_case_data.get('weight')
        self.hidden = test_case_data.get('hidden')

    def teardown(self):
        os.remove(self.submit_code_path)
        if self.files:
            delete_files(self.files)

    def compile_code(self):
        self.submit_code_path = self.create_submit_code_file('Test.sh')
        if self.file_paths:
            self.files = copy_files(self.file_paths)
        if not isfile(self.submit_code_path):
            msg = "No file at %s or Incorrect path" % self.submit_code_path
            return False, msg
        self.user_answer = self.user_answer.replace("\r", "")
        self.write_to_submit_code_file(self.submit_code_path, self.user_answer)

    def check_code(self):
        success = False
        mark_fraction = 0.0

        self.expected_input = str(self.expected_input).replace('\r', '')
        proc = subprocess.Popen("bash ./Test.sh",
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                preexec_fn=os.setpgrp
                                )
        success, err = self.evaluate_stdio(self.user_answer, proc,
                                           self.expected_input,
                                           self.expected_output
                                           )
        mark_fraction = 1.0 if self.partial_grading and success else 0.0
        return success, err, mark_fraction
