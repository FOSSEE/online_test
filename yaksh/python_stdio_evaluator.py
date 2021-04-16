import sys
from contextlib import contextmanager

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# Local imports
from .file_utils import copy_files, delete_files
from .base_evaluator import BaseEvaluator
from .error_messages import compare_outputs


@contextmanager
def redirect_stdout():
    new_target = StringIO()
    old_target, sys.stdout = sys.stdout, new_target  # replace sys.stdout
    try:
        yield new_target  # run some code with the replaced stdout
    finally:
        sys.stdout = old_target  # restore to the previous value


class PythonStdIOEvaluator(BaseEvaluator):
    """Tests the Python code obtained from Code Server"""
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
        # Delete the created file.
        if self.files:
            delete_files(self.files)

    def compile_code(self):
        if self.file_paths:
            self.files = copy_files(self.file_paths)
        submitted = compile(self.user_answer, '<string>', mode='exec')
        self.expected_output = self.expected_output.replace('\r', '')
        if self.expected_input:
            self.expected_input = self.expected_input.replace('\r', '')
            input_buffer = StringIO()
            input_buffer.write(self.expected_input)
            input_buffer.seek(0)
            sys.stdin = input_buffer
        with redirect_stdout() as output_buffer:
            exec_scope = {}
            exec(submitted, exec_scope)
        self.output_value = output_buffer.getvalue()
        return self.output_value

    def check_code(self):
        mark_fraction = self.weight
        success, err = compare_outputs(self.expected_output,
                                       self.output_value,
                                       self.expected_input
                                       )
        return success, err, mark_fraction
