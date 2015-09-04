import unittest
import os
from testapp.yaksh_app.cpp_code_evaluator import CppCodeEvaluator
from testapp.yaksh_app.settings import SERVER_TIMEOUT

class CEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "C"
        self.ref_code_path = "c_cpp_files/main.cpp"
        self.in_dir = "/tmp"
        self.test_case_data = []
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)
        self.test = None

    def test_correct_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b;}"
        get_class = CppCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_compilation_error(self):
        user_answer = "int add(int a, int b)\n{return a+b}"
        get_class = CppCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()

        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "int add(int a, int b)\n{while(1>0){}}"
        get_class = CppCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()
 
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)


###############################################################################
class CppEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "CPP"
        self.ref_code_path = "c_cpp_files/main.cpp"
        self.in_dir = "/tmp"
        self.test_case_data = []
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)
        self.test = None

    def test_correct_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b;}"
        get_class = CppCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_compilation_error(self):
        user_answer = "int add(int a, int b)\n{return a+b}"
        get_class = CppCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()

        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "int add(int a, int b)\n{while(1>0){}}"
        get_class = CppCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()
 
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)

if __name__ == '__main__':
    unittest.main()
