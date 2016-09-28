from __future__ import unicode_literals

# Local imports
from .code_evaluator import CodeEvaluator
import os
import signal
# Local imports
from code_evaluator import CodeEvaluator, TimeoutException


class StdIOEvaluator(CodeEvaluator):
    def setup(self):
        super(StdIOEvaluator, self).setup()
        pass

    def teardown(self):
        super(StdIOEvaluator, self).teardown()
        pass

    def evaluate_stdio(self, user_answer, proc, expected_input, expected_output):
        success = False
        ip = expected_input.replace(",", " ")
        encoded_input = '{0}\n'.format(ip).encode('utf-8')
        user_output_bytes, output_err_bytes = proc.communicate(encoded_input)
        user_output = user_output_bytes.decode('utf-8')
        output_err = output_err_bytes.decode('utf-8')
        try:
            user_output, output_err = proc.communicate(input='{0}\n'.format(ip))
        except TimeoutException:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            raise
        expected_output = expected_output.replace("\r", "")
        if not expected_input:
            error_msg = "Expected Output is {0} ".\
                        format(repr(expected_output))
        else:
            error_msg = " Given Input is\n {0} \n Expected Output is {1} ".\
                        format(expected_input, repr(expected_output))
        if output_err == '':
            if user_output == expected_output:
                success, err = True, "Correct answer"
            else:
                err = " Incorrect answer\n" + error_msg +\
                      "\n Your output is {0}".format(repr(user_output))
        else:
            err = "Error:\n {0}".format(output_err)
        return success, err
