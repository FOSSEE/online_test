from yaksh.error_messages import compare_outputs


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
    error_msg = msg.get('error_msg')
    assert not success
    m = ("Incorrect Answer: We had expected 1 number of lines. " +
         "We got 2 number of lines.")
    assert m == error_msg

    exp = "5\n5\n"
    given = "5\n6"
    success, msg = compare_outputs(given, exp)
    error_msg = msg.get('error_msg')
    m = "Incorrect Answer: Line number(s) 2 did not match."
    assert not success
    assert m == error_msg
