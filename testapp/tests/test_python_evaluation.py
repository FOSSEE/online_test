import unittest
import os
from testapp.yaksh_app.python_code_evaluator import PythonCodeEvaluator
from testapp.yaksh_app.settings import SERVER_TIMEOUT

class PythonEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "Python"
        self.test = None
        self.test_case_data = [{"func_name": "add", 
                                 "expected_answer": "5", 
                                 "test_id": u'null', 
                                 "pos_args": ["3", "2"], 
                                 "kw_args": {}
                                }]
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        user_answer = "def add(a, b):\n\treturn a + b"""
        get_class = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = get_class.evaluate()
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "def add(a, b):\n\treturn a - b"
        test_case_data = [{"func_name": "add", 
                                 "expected_answer": "5", 
                                 "test_id": u'null', 
                                 "pos_args": ["3", "2"], 
                                 "kw_args": {}
                                }]
        get_class = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = get_class.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), "AssertionError  in: assert add(3, 2) == 5")

    def test_infinite_loop(self):
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"""
        test_case_data = [{"func_name": "add", 
                                 "expected_answer": "5", 
                                 "test_id": u'null', 
                                 "pos_args": ["3", "2"], 
                                 "kw_args": {}
                                }]
        get_class = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = get_class.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)

if __name__ == '__main__':
    unittest.main()
