#!/usr/bin/env python
from __future__ import unicode_literals
import subprocess
import os
from os.path import isfile

#Local imports
from .stdio_evaluator import StdIOEvaluator
from .file_utils import copy_files, delete_files


class CppStdioEvaluator(StdIOEvaluator):
    """Evaluates C StdIO based code"""

    def setup(self):
        super(CppStdioEvaluator, self).setup()
        self.submit_code_path = self.create_submit_code_file('main.c')

    def teardown(self):
        os.remove(self.submit_code_path)
        if self.files:
            delete_files(self.files)
        super(CppStdioEvaluator, self).teardown()

    def set_file_paths(self):
        user_output_path = os.getcwd() + '/output_file'
        ref_output_path = os.getcwd() + '/executable'
        return user_output_path, ref_output_path

    def get_commands(self, user_output_path, ref_output_path):
        compile_command = 'g++  {0} -c -o {1}'.format(self.submit_code_path,
                                                      user_output_path)
        compile_main = 'g++ {0} -o {1}'.format(user_output_path,
                                               ref_output_path)
        return compile_command, compile_main

    def compile_code(self, user_answer, file_paths, expected_input, expected_output):

        self.files = []
        if file_paths:
            self.files = copy_files(file_paths)
        if not isfile(self.submit_code_path):
            msg = "No file at %s or Incorrect path" % self.submit_code_path
            return False, msg
        self.write_to_submit_code_file(self.submit_code_path, user_answer)
        self.user_output_path, self.ref_output_path = self.set_file_paths()
        self.compile_command, self.compile_main = self.get_commands(
            self.user_output_path,
            self.ref_output_path
            )
        self.compiled_user_answer = self._run_command(self.compile_command,
                                                      shell=True,
                                                      stdin=subprocess.PIPE,
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE
                                                      )
        self.compiled_test_code = self._run_command(self.compile_main,
                                                    shell=True,
                                                    stdin=subprocess.PIPE,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE
                                                    )
        return self.compiled_user_answer, self.compiled_test_code

    def check_code(self, user_answer, file_paths, expected_input, expected_output):
        success = False
        proc, stdnt_out, stdnt_stderr = self.compiled_user_answer
        stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)
        if stdnt_stderr == '':
            proc, main_out, main_err = self.compiled_test_code
            main_err = self._remove_null_substitute_char(main_err)
            if main_err == '':
                proc = subprocess.Popen("./executable",
                                        shell=True,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        preexec_fn=os.setpgrp
                                        )
                success, err = self.evaluate_stdio(user_answer, proc,
                                                   expected_input,
                                                   expected_output
                                                   )
                os.remove(self.ref_output_path)
            else:
                err = "Error:"
                try:
                    error_lines = main_err.splitlines()
                    for e in error_lines:
                        if ':' in e:
                            err = err + "\n" + e.split(":", 1)[1]
                        else:
                            err = err + "\n" + e
                except:
                        err = err + "\n" + main_err
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
            except:
                err = err + "\n" + stdnt_stderr
        return success, err
