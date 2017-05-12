import sys
from contextlib import contextmanager

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

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

def _incorrect_user_lines(exp_lines, user_lines):
    err_line_no = []
    for i, (expected_line, user_line) in enumerate(zip_longest(exp_lines, user_lines)):
        if not user_line or not expected_line:
            err_line_no.append(i)
        else:
            if user_line.strip() != expected_line.strip():
                err_line_no.append(i)
    return err_line_no

def compare_outputs(expected_output, user_output,given_input=None):
    given_lines = user_output.splitlines()
    exp_lines = expected_output.splitlines()
    # if given_input:
    #     given_input =  given_input.splitlines()
    msg = {"given_input":given_input,
           "expected_output": exp_lines,
           "user_output":given_lines
            }
    ng = len(given_lines)
    ne = len(exp_lines)
    if ng != ne:
        err_line_no = _incorrect_user_lines(exp_lines, given_lines)
        msg["error_no"] = err_line_no
        msg["error"] = "We had expected {0} number of lines. We got {1} number of lines.".format(ne, ng)
        return False, msg
    else:
        err_line_no = _incorrect_user_lines(exp_lines, given_lines)
        if err_line_no:
            msg["error_no"] = err_line_no
            msg["error"] = "Line number(s) {0} did not match."\
                            .format(", ".join(map(str,[x+1 for x in err_line_no])))
            return False, msg
        else:
            msg["error"] = "Correct answer"
            return True, msg


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
        success, err = compare_outputs(self.expected_output,
                                       self.output_value,
                                       self.expected_input
                                       )
        return success, err, mark_fraction
