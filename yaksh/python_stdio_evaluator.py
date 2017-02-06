import sys
from contextlib import contextmanager


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# Local imports
from .file_utils import copy_files, delete_files
from .base_evaluator import BaseEvaluator


@contextmanager
def redirect_stdout():
    new_target = StringIO()
    old_target, sys.stdout = sys.stdout, new_target  # replace sys.stdout
    try:
        yield new_target  # run some code with the replaced stdout
    finally:
        sys.stdout = old_target  # restore to the previous value


def _show_expected_given(expected, given):
    return "Expected:\n{0}\nGiven:\n{1}\n".format(expected, given)


def compare_outputs(given, expected):
    given_lines = given.splitlines()
    ng = len(given_lines)
    exp_lines = expected.splitlines()
    ne = len(exp_lines)
    if ng != ne:
        msg = "ERROR: Got {0} lines in output, we expected {1}.\n".format(
            ng, ne
        )
        msg += _show_expected_given(expected, given)
        return False, msg
    else:
        for i, (given_line, expected_line) in \
           enumerate(zip(given_lines, exp_lines)):
            if given_line.strip() != expected_line.strip():
                msg = "ERROR:\n"
                msg += _show_expected_given(expected, given)
                msg += "\nError in line %d of output.\n" % (i+1)
                msg += "Expected line {0}:\n{1}\nGiven line {0}:\n{2}\n"\
                       .format(
                           i+1, expected_line, given_line
                       )
                return False, msg
    return True, "Correct answer."


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

    def teardown(self):
        # Delete the created file.
        if self.files:
            delete_files(self.files)

    def compile_code(self):
        if self.file_paths:
            self.files = copy_files(self.file_paths)
        submitted = compile(self.user_answer, '<string>', mode='exec')
        if self.expected_input:
            input_buffer = StringIO()
            input_buffer.write(self.expected_input)
            input_buffer.seek(0)
            sys.stdin = input_buffer
        with redirect_stdout() as output_buffer:
            exec_scope = {}
            exec(submitted, exec_scope)
        self.output_value = output_buffer.getvalue().rstrip("\n")
        return self.output_value

    def check_code(self):
        mark_fraction = self.weight
        success, err = compare_outputs(self.output_value, self.expected_output)
        return success, err, mark_fraction
