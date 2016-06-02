#!/usr/bin/env python
import subprocess
import os
from os.path import isfile

#local imports
from code_evaluator import CodeEvaluator
from stdio_evaluator import Evaluator


class JavaStdioEvaluator(CodeEvaluator):
    """Evaluates Java StdIO based code"""

    def setup(self):
        super(JavaStdioEvaluator, self).setup()
        self.submit_code_path = self.create_submit_code_file('Test.java')

    def teardown(self):
        super(JavaStdioEvaluator, self).teardown()
        os.remove(self.submit_code_path)

    def set_file_paths(self, directory, file_name):
        output_path = "{0}{1}.class".format(directory, file_name)
        return output_path

    def get_commands(self):
        compile_command = 'javac {0}'.format(self.submit_code_path)

        return compile_command

    def compile_code(self, user_answer, expected_input, expected_output):
        if not isfile(self.submit_code_path):
            msg = "No file at %s or Incorrect path" % self.submit_code_path
            return False, msg
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

    def check_code(self, user_answer, expected_input, expected_output):
        success = False
        proc, stdnt_out, stdnt_stderr = self.compiled_user_answer
        stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)
        if stdnt_stderr == '' or "error" not in stdnt_stderr:
            proc = subprocess.Popen("java Test",
                                    shell=True,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
            evaluator = Evaluator()
            success, err = evaluator.evaluate(user_answer, proc,
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

        return success, err
