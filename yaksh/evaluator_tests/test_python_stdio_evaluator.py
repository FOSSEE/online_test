from textwrap import dedent

from yaksh.python_stdio_evaluator import compare_outputs


def test_compare_outputs():
    exp = "5\n5\n"
    given = "5\n5\n"
    success, msg = compare_outputs(given, exp)
    assert success

    exp = "5\n5\n"
    given = "5\n5"
    success, msg = compare_outputs(given, exp)
    assert success

    exp = "5\r5"
    given = "5\n5"
    success, msg = compare_outputs(given, exp)
    assert success

    exp = " 5 \r 5 "
    given = "  5  \n  5  "
    success, msg = compare_outputs(given, exp)
    assert success

    exp = "5\n5\n"
    given = "5 5"
    success, msg = compare_outputs(given, exp)
    assert not success
    m = dedent("""\
    ERROR: Got 1 lines in output, we expected 2.
    Expected:
    5
    5

    Given:
    5 5
    """)
    assert m == msg

    exp = "5\n5\n"
    given = "5\n6"
    success, msg = compare_outputs(given, exp)
    assert not success
    m = dedent("""\
    ERROR:
    Expected:
    5
    5

    Given:
    5
    6

    Error in line 2 of output.
    Expected line 2:
    5
    Given line 2:
    6
    """)
    assert m == msg
