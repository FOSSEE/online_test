import unittest
import os
from yaksh.cpp_code_evaluator import CppCodeEvaluator
from yaksh.settings import SERVER_TIMEOUT

class CEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.test_case_data = ["c_cpp_files/main.cpp"]
        self.in_dir = "/tmp"
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b;}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertEquals(result.get('error'), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "int add(int a, int b)\n{return a-b;}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect:", result.get('error'))
        self.assertTrue(result.get('error').splitlines > 1)

    def test_compilation_error(self):
        user_answer = "int add(int a, int b)\n{return a+b}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "int add(int a, int b)\n{while(1>0){}}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)

if __name__ == '__main__':
    unittest.main()
