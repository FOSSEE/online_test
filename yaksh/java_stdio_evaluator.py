#!/usr/bin/env python
from __future__ import unicode_literals
import subprocess
import os
from os.path import isfile

# Local imports
from .stdio_evaluator import StdIOEvaluator
from .file_utils import copy_files, delete_files
from .grader import CompilationError


class JavaStdIOEvaluator(StdIOEvaluator):
    """Evaluates Java StdIO based code"""
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
        if os.path.exists(self.submit_code_path):
            os.remove(self.submit_code_path)
        if self.files:
            delete_files(self.files)

    def set_file_paths(self, directory, file_name):
        output_path = "{0}{1}.class".format(directory, file_name)
        return output_path

    def get_commands(self):
        compile_command = 'javac {0}'.format(self.submit_code_path)
        return compile_command

    def compile_code(self):
        self.submit_code_path = self.create_submit_code_file('Test.java')
        if not isfile(self.submit_code_path):
            msg = "No file at %s or Incorrect path" % self.submit_code_path
            return False, msg
        if self.file_paths:
            self.files = copy_files(self.file_paths)
        user_code_directory = os.getcwd() + '/'
        self.write_to_submit_code_file(self.submit_code_path, self.user_answer)
        self.user_output_path = self.set_file_paths(user_code_directory,
                                                    'Test'
                                                    )
        self.compile_command = self.get_commands()
        self.compiled_user_answer = self._run_command(self.compile_command,
                                                      shell=True,
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE
                                                      )
        return self.compiled_user_answer

    def check_code(self):
        success = False
        mark_fraction = 0.0
        proc, stdnt_out, stdnt_stderr = self.compiled_user_answer
        stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)
        if stdnt_stderr == '' or "error" not in stdnt_stderr:
            proc = subprocess.Popen("java Test",
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
            os.remove(self.user_output_path)
        else:
            err = "Compilation Error:"
            try:
                error_lines = stdnt_stderr.splitlines()
                for e in error_lines:
                    if ':' in e:
                        err = err + "\n" + e.split(":", 1)[1]
                    else:
                        err = err + "\n" + e
            except Exception:
                err = err + "\n" + stdnt_stderr
            raise CompilationError(err)
        mark_fraction = 1.0 if self.partial_grading and success else 0.0
        return success, err, mark_fraction
