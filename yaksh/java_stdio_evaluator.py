#!/usr/bin/env python
from __future__ import unicode_literals
import subprocess
import os
from os.path import isfile

#Local imports
from .stdio_evaluator import StdIOEvaluator
from .file_utils import copy_files, delete_files


class JavaStdioEvaluator(StdIOEvaluator):
    """Evaluates Java StdIO based code"""

    def setup(self):
        super(JavaStdioEvaluator, self).setup()
        self.files = []
        self.submit_code_path = self.create_submit_code_file('Test.java')

    def teardown(self):
        os.remove(self.submit_code_path)
        if self.files:
            delete_files(self.files)
        super(JavaStdioEvaluator, self).teardown()

    def set_file_paths(self, directory, file_name):
        output_path = "{0}{1}.class".format(directory, file_name)
        return output_path

    def get_commands(self):
        compile_command = 'javac {0}'.format(self.submit_code_path)
        return compile_command

    def compile_code(self, user_answer, file_paths, expected_input, expected_output, weightage):
        if not isfile(self.submit_code_path):
            msg = "No file at %s or Incorrect path" % self.submit_code_path
            return False, msg
        if file_paths:
            self.files = copy_files(file_paths)
        user_code_directory = os.getcwd() + '/'
        self.write_to_submit_code_file(self.submit_code_path, user_answer)
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

    def check_code(self, user_answer, file_paths, partial_grading,
        expected_input, expected_output, weightage):
        success = False
        test_case_weightage = 0.0
        proc, stdnt_out, stdnt_stderr = self.compiled_user_answer
        stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)
        if stdnt_stderr == '' or "error" not in stdnt_stderr:
            proc = subprocess.Popen("java Test",
                                    shell=True,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
            success, err = self.evaluate_stdio(user_answer, proc,
                                               expected_input,
                                               expected_output
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
            except:
                err = err + "\n" + stdnt_stderr
        test_case_weightage = float(weightage) if partial_grading and success else 0.0
        return success, err, test_case_weightage
