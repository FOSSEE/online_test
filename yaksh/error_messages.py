try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest


def prettify_exceptions(exception, message, traceback=None,
                        testcase=None, line_no=None):
    err = {"type": "assertion",
           "exception": exception,
           "traceback": traceback,
           "message": message
           }
    ignore_traceback = ['RuntimeError', 'RecursionError',
                        "CompilationError", "TestCaseError"
                        ]
    if exception in ignore_traceback:
        err["traceback"] = None

    if exception == 'AssertionError':
        value = ("Expected answer from the" +
                 " test case did not match the output")
        if message:
            err["message"] = message
        else:
            err["message"] = value
        err["traceback"] = None
    err["test_case"] = testcase
    err["line_no"] = line_no
    return err


def _get_incorrect_user_lines(exp_lines, user_lines):
    err_line_numbers = []
    for line_no, (expected_line, user_line) in \
            enumerate(zip_longest(exp_lines, user_lines)):
        if user_line != expected_line:
            err_line_numbers.append(line_no)
    return err_line_numbers


def compare_outputs(expected_output, user_output, given_input=None):
    given_lines = user_output.splitlines()
    exp_lines = expected_output.splitlines()
    msg = {"type": "stdio",
           "given_input": given_input,
           "expected_output": exp_lines,
           "user_output": given_lines
           }
    ng = len(given_lines)
    ne = len(exp_lines)
    err_line_numbers = _get_incorrect_user_lines(exp_lines, given_lines)
    msg["error_line_numbers"] = err_line_numbers
    if ng != ne:
        msg["error_msg"] = ("Incorrect Answer: " +
                            "We had expected {} number of lines. ".format(ne) +
                            "We got {} number of lines.".format(ng)
                            )
        return False, msg
    else:
        if err_line_numbers:
            msg["error_msg"] = ("Incorrect Answer: " +
                                "Line number(s) {0} did not match."
                                .format(", ".join(
                                    map(str, [x+1 for x in err_line_numbers])
                                )))
            return False, msg
        else:
            msg["error_msg"] = "Correct Answer"
            return True, msg
