import unittest
import os
from testapp.yaksh_app.bash_code_evaluator import BashCodeEvaluator
from testapp.yaksh_app.settings import SERVER_TIMEOUT

class BashEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "bash"
        self.ref_code_path = "bash_files/sample.sh,bash_files/sample.args"
        self.in_dir = "/tmp"
        self.test_case_data = []
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)
        self.test = None

    def test_correct_answer(self):
        user_answer = "#!/bin/bash\n[[ $# -eq 2 ]] && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))"
        get_class = BashCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_error(self):
        user_answer = "#!/bin/bash\n[[ $# -eq 2 ]] && echo $(( $1 - $2 )) && exit $(( $1 - $2 ))"
        get_class = BashCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()

        self.assertFalse(result.get("success"))
        self.assertTrue("Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "#!/bin/bash\nwhile [ 1 ] ; do echo "" > /dev/null ; done"
        get_class = BashCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()

        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)

if __name__ == '__main__':
    unittest.main()
