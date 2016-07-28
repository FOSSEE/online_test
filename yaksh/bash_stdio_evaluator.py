#!/usr/bin/env python
import subprocess
import os
from os.path import isfile

#local imports
from code_evaluator import CodeEvaluator
from stdio_evaluator import Evaluator


class BashStdioEvaluator(CodeEvaluator):
    """Evaluates Bash StdIO based code"""

    def setup(self):
        super(BashStdioEvaluator, self).setup()
        self.submit_code_path = self.create_submit_code_file('Test.sh')

    def teardown(self):
        super(BashStdioEvaluator, self).teardown()
        os.remove(self.submit_code_path)

    def compile_code(self, user_answer, expected_input, expected_output):
        if not isfile(self.submit_code_path):
            msg = "No file at %s or Incorrect path" % self.submit_code_path
            return False, msg
        user_code_directory = os.getcwd() + '/'
        user_answer = user_answer.replace("\r", "")
        self.write_to_submit_code_file(self.submit_code_path, user_answer)

    def check_code(self, user_answer, expected_input, expected_output):
        success = False
        expected_input = str(expected_input).replace('\r', '')
        proc = subprocess.Popen("bash ./Test.sh",
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
        return success, err
