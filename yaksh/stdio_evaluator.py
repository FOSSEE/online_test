from __future__ import unicode_literals
import os
import signal

# Local imports
from .base_evaluator import BaseEvaluator
from .grader import TimeoutException
from .error_messages import compare_outputs


class StdIOEvaluator(BaseEvaluator):
    def evaluate_stdio(self, user_answer, proc,
                       expected_input, expected_output):
        success = False
        try:
            if expected_input:
                ip = expected_input.replace(",", " ")
                encoded_input = '{0}\n'.format(ip).encode('utf-8')
                user_output_bytes, output_err_bytes = proc.communicate(
                                                           encoded_input
                                                           )
            else:
                user_output_bytes, output_err_bytes = proc.communicate()
            user_output = user_output_bytes.decode('utf-8')
        except TimeoutException:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            raise
        expected_output = expected_output.replace("\r", "")
        success, err = compare_outputs(expected_output,
                                       user_output,
                                       expected_input
                                       )
        return success, err
