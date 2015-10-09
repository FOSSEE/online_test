import unittest
import os
from yaksh import code_evaluator as evaluator
from yaksh.java_code_evaluator import JavaCodeEvaluator


class JavaEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "java"
        self.ref_code_path = "java_files/main_square.java"
        self.in_dir = "/tmp"
        self.test_case_data = []
        evaluator.SERVER_TIMEOUT = 9
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in "
                            "your code.").format(evaluator.SERVER_TIMEOUT)
        self.test = None

    def tearDown(self):
        evaluator.SERVER_TIMEOUT = 2

    def test_correct_answer(self):
        user_answer = "class Test {\n\tint square_num(int a) {\n\treturn a*a;\n\t}\n}"
        get_class = JavaCodeEvaluator(self.test_case_data, self.test,
                                         self.language, user_answer,
                                         self.ref_code_path, self.in_dir)
        result = get_class.evaluate()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_error(self):
        user_answer = "class Test {\n\tint square_num(int a) {\n\treturn a*a"
        get_class = JavaCodeEvaluator(self.test_case_data, self.test,
                                         self.language, user_answer,
                                         self.ref_code_path, self.in_dir)
        result = get_class.evaluate()
 
        self.assertFalse(result.get("success"))
        self.assertTrue("Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "class Test {\n\tint square_num(int a) {\n\t\twhile(0==0){\n\t\t}\n\t}\n}"
        get_class = JavaCodeEvaluator(self.test_case_data, self.test,
                                         self.language, user_answer,
                                         self.ref_code_path, self.in_dir)
        result = get_class.evaluate()
 
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)

if __name__ == '__main__':
    unittest.main()
