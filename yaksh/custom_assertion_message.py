from nose.tools import assert_almost_equal

try:
    import numpy as np
    from numpy.testing import assert_allclose
except:
    np = None
    assert_allclose = None


class CustomAssertionError(AssertionError):
    pass


def safe_repr(value):
    try:
        return repr(value)
    except Exception:
        return "<unrepresentable value>"


def is_numpy_value(value):
    return np is not None and isinstance(value, np.ndarray)


def _raise_eval_error(expression, exc):
    message = (
        "We called `%s`.\n"
        "The code raised an error instead of returning the expected result.\n"
        "Error: %s: %s\n"
        "Kindly debug your code."
        % (expression, type(exc).__name__, str(exc))
    )

    raise CustomAssertionError(message)


def _raise_comparison_error(expression, actual, exc):
    message = (
        "We called `%s`.\n"
        "Your code returned: %s\n"
        "Comparing your output with the expected output raised an error.\n"
        "Comparison error: %s: %s"
        % (expression, safe_repr(actual), type(exc).__name__, str(exc))
    )

    raise CustomAssertionError(message)


def _raise_failure_message(expression, actual, expected, reveal_expected=True,
                           hint=None, tolerance=None, details=None):
    lines = [
        "We called `%s`." % expression,
    ]

    if reveal_expected:
        if tolerance is None:
            lines.append("Expected output: %s" % safe_repr(expected))
        else:
            lines.append(
                "Expected output: %s with tolerance ±%s"
                % (safe_repr(expected), safe_repr(tolerance))
            )
    else:
        lines.append("The result did not match the expected behavior.")

    lines.append("Your code returned: %s" % safe_repr(actual))

    if details:
        lines.append("Details: %s" % details)

    if hint is not None:
        lines.append("Hint: %s" % hint)

    raise CustomAssertionError("\n".join(lines))


def _set_scope(g, l):
    if g is None:
        globals_ = {}
    if l is None:
        locals_ = {}


def check_equal(expression, expected, reveal_expected=True, hint=None,
        globals_=None, locals_=None):
    """
    Simple usage:

        check_equal("add(1, 2)", 3)

    It evaluates the expression string, compares result with expected,
    and raises readable feedback if it fails.

    Raises:
        CustomAssertionError:
            Raised when the student's result does not match the expected result,
            or when the student's code raises an exception while being tested.

    Returns:
        None:
            Returns silently when the actual result equals the expected result.
    """

    _set_scope(globals_, locals_)

    try:
        actual = eval(expression, globals_, locals_)
    except Exception as e:
        raise _raise_eval_error(expression, e)

    try:
        matched = actual == expected
        if matched:
            return
    except Exception as e:
        raise _raise_comparison_error(expression, actual, e)

    raise _raise_failure_message(expression, actual, expected,
        reveal_expected, hint)


def check_almost_equal(expression, expected, tolerance=0.001, rtol=0,
    reveal_expected=True, hint=None, globals_=None, locals_=None):

    _set_scope(globals_, locals_)

    try:
        actual = eval(expression, globals_, locals_)
    except Exception as e:
        raise _raise_eval_error(expression, e)

    try:
        if is_numpy_value(actual) or is_numpy_value(expected):
            assert_allclose(actual, expected, atol=tolerance, rtol=rtol)
        else:
            assert_almost_equal(actual, expected, delta=tolerance)
    except AssertionError as e:
        raise _raise_failure_message(expression, actual, expected,
            reveal_expected, hint, tolerance, details=str(e))
    except Exception as e:
        raise _raise_comparison_error(expression, safe_repr(actual), e)
