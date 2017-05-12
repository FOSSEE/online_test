from __future__ import unicode_literals
import os
import signal

# Local imports
from .base_evaluator import BaseEvaluator
from .grader import TimeoutException
from .compare_stdio import CompareOutputs


class StdIOEvaluator(BaseEvaluator):
    def evaluate_stdio(self, user_answer, proc, expected_input, expected_output):
        success = False
        ip = expected_input.replace(",", " ")
        encoded_input = '{0}\n'.format(ip).encode('utf-8')
        try:
            user_output_bytes, output_err_bytes = proc.communicate(encoded_input)
            user_output = user_output_bytes.decode('utf-8')
            output_err = output_err_bytes.decode('utf-8')
        except TimeoutException:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            raise
        expected_output = expected_output.replace("\r", "")
        compare = CompareOutputs()
        success, err = compare.compare_outputs(expected_output,
                                               user_output,
                                               expected_input
                                               )
        return success, err
