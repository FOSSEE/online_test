import unittest
import os
from yaksh.python_code_evaluator import PythonCodeEvaluator
from yaksh.settings import SERVER_TIMEOUT

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

    def test_correct_answer(self):
        user_answer = "def add(a, b):\n\treturn a + b"
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "def add(a, b):\n\treturn a - b"
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), "AssertionError  in: assert add(3, 2) == 5")

    def test_infinite_loop(self):
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"
        timeout_msg = ("Code took more than {0} seconds to run. "
                       "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), timeout_msg)

    def test_syntax_error(self):
        user_answer = "def add(a, b);\n\treturn a+b"
        syntax_error_msg = ('Traceback (most recent call last):\n  File '
                            '"<string>", line 1\n    def add(a, b);\n   '
                            '              ^\nSyntaxError: invalid syntax\n')
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), syntax_error_msg)

    def test_indent_error(self):
        user_answer = "def add(a, b):\nreturn a+b"
        indent_error_msg = ('Traceback (most recent call last):\n  '
                            'File "<string>", line 2\n    '
                            'return a+b\n         ^\nIndentationError: '
                            'expected an indented block\n')
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), indent_error_msg)

    def test_name_error(self):
        user_answer = ""
        name_error_msg = ("Traceback (most recent call last):\nNameError: "
                          "name 'add' is not defined\n")
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), name_error_msg)

    def test_recursion_error(self):
        user_answer = ("def fact(a):\n\tif a == 0:\n\t\treturn fact(1)"
                       "\n\telse:\n\t\treturn a * fact(a-1)")
        self.test_case_data = [{"func_name": "fact",
                                "expected_answer": "24",
                                "test_id": u'null',
                                "pos_args": ["4"],
                                "kw_args": {}
                                }]
        recursion_error_msg = ('Traceback (most recent call last):\nRuntimeError: '
                               'maximum recursion depth exceeded\n')
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), recursion_error_msg)

    def test_type_error(self):
        user_answer = "def add(a):\n\treturn a+b"
        type_error_msg = ("Traceback (most recent call last):\nTypeError: "
                          "add() takes exactly 1 argument (2 given)\n")
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), type_error_msg)

    def test_value_error(self):
        user_answer = "def split(line):\n\t[ key, value ] = line.split()"
        type_error_msg = ("Traceback (most recent call last):\nValueError: "
                          "need more than 1 value to unpack\n")
        self.test_case_data = [{"func_name": "split",
                                "expected_answer": "Hello",
                                "test_id": u'null',
                                "pos_args": ["'Hello'"],
                                "kw_args": {}
                                }]
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        """add variable name as get evaluator instead of evaluator"""
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), type_error_msg)

if __name__ == '__main__':
    unittest.main()
