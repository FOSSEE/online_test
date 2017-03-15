from __future__ import unicode_literals

# Local imports
from .base_evaluator import BaseEvaluator


class StdIOEvaluator(BaseEvaluator):
    def evaluate_stdio(self, user_answer, proc, expected_input, expected_output):
        success = False
        ip = expected_input.replace(",", " ")
        encoded_input = '{0}\n'.format(ip).encode('utf-8')
        user_output_bytes, output_err_bytes = proc.communicate(encoded_input)
        user_output = user_output_bytes.decode('utf-8')
        output_err = output_err_bytes.decode('utf-8')
        expected_output = expected_output.replace("\r", "")
        if not expected_input:
            error_msg = "Expected Output is\n{0} ".\
                        format(str(expected_output))
        else:
            error_msg = "Given Input is\n{0}\nExpected Output is\n{1}".\
                        format(expected_input, str(expected_output))
        if output_err == '':
            if user_output == expected_output:
                success, err = True, None
            else:
                err = "Incorrect answer:\n" + error_msg +\
                      "\nYour output is\n{0}".format(str(user_output))
        else:
            err = "Error:\n{0}".format(output_err)
        return success, err
