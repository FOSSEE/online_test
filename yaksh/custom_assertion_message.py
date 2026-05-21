class CustomAssertionError(AssertionError):
    pass

def safe_repr(value):
    try:
        return repr(value)
    except Exception:
        return "<unrepresentable value>"

def check_equal(target_name, input_description, actual_callable, expected,
                reveal_expected=False, hint=None):
    """
    Compare a student's actual result with an expected result and raise a
    readable assertion error if they do not match.

    Parameters:
        target_name (str):
            The name of the function or method being tested.
            Examples: "is_palindrome", "add", "MyClass.method".

        input_description (str):
            A human-readable description of the input or object state used in
            the test.
            Examples: '"hello"', "2, 3".

        actual_callable:
            A callable, usually a lambda, that runs the student's code and
            returns the actual result.
            Example: lambda: is_palindrome("hello")

            A direct value may also be passed, but a callable is preferred
            because it allows this helper to catch runtime errors and convert
            them into readable feedback.

        expected:
            The expected result to compare against the student's actual result.

        hint (str, optional):
            Optional guidance shown to the student when the test fails.

        reveal_expected (bool, optional):
            If True, include the expected output in the feedback message.
            If False, hide the expected output and only say that the result did
            not match the expected behavior.

    Raises:
        CustomAssertionError:
            Raised when the student's result does not match the expected result,
            or when the student's code raises an exception while being tested.

    Returns:
        None:
            Returns silently when the actual result equals the expected result.
    """

    if '.' in target_name:
        target_type = "method"
    else:
        target_type = "function"

    first_line = "Your %s `%s` was tested using %s." % (
            target_type, target_name, input_description,
        )
    try:
        if callable(actual_callable):
            actual = actual_callable()
        else:
            actual = actual_callable
    except Exception as e:
        message = (
            "%s\n"
            "The code raised an error instead of returning "
            "the expected result.\n"
            "Error observed: %s: %s\n"
            "Kindly debug your code."%(first_line, type(e).__name__, str(e),)
        )

        raise CustomAssertionError(message)

    if actual == expected:
        return

    lines = [first_line]

    if reveal_expected:
        lines.append("Expected output: %s" % safe_repr(expected))
    else:
        lines.append("The result did not match the expected behaviour")

    lines.append("Your code returned: %s" % safe_repr(actual))

    if hint is not None:
        lines.append("Hint: %s" % hint)

    message = "\n".join(lines)

    raise CustomAssertionError(message)
