import unittest
import os
from yaksh.python_code_evaluator import PythonCodeEvaluator
from yaksh.settings import SERVER_TIMEOUT
from textwrap import dedent


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
        user_answer = dedent("""
        def add(a, b):
            return a + b
        """)
        get_evaluator = PythonCodeEvaluator(self.test_case_data, self.test,
                                            self.language, user_answer)
        result = get_evaluator.evaluate()
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = dedent("""
        def add(a, b):
            return a - b
        """)
        get_evaluator = PythonCodeEvaluator(self.test_case_data, self.test,
                                            self.language, user_answer)
        result = get_evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), "AssertionError  in: assert add(3, 2) == 5")

    def test_infinite_loop(self):
        user_answer = dedent("""
        def add(a, b):
            while True:
                pass
        """)
        timeout_msg = ("Code took more than {0} seconds to run. "
                       "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)
        get_evaluator = PythonCodeEvaluator(self.test_case_data, self.test,
                                            self.language, user_answer)
        result = get_evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), timeout_msg)

    def test_syntax_error(self):
        user_answer = dedent("""
        def add(a, b);
            return a + b
        """)
        syntax_error_msg = ["Traceback", "call", "File", "line", "<string>",
                            "SyntaxError", "invalid syntax"]
        get_evaluator = PythonCodeEvaluator(self.test_case_data, self.test,
                                            self.language, user_answer)
        result = get_evaluator.evaluate()
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(5, len(err))
        for msg in syntax_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_indent_error(self):
        user_answer = dedent("""
        def add(a, b):
        return a + b
        """)
        indent_error_msg = ["Traceback", "call", "File", "line", "<string>",
                            "IndentationError", "indented block"]
        get_evaluator = PythonCodeEvaluator(self.test_case_data, self.test,
                                            self.language, user_answer)
        result = get_evaluator.evaluate()
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(5, len(err))
        for msg in indent_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_name_error(self):
        user_answer = ""
        name_error_msg = ["Traceback", "call", "NameError", "name", "defined"]
        get_evaluator = PythonCodeEvaluator(self.test_case_data, self.test,
                                            self.language, user_answer)
        result = get_evaluator.evaluate()
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(2, len(err))
        for msg in name_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_recursion_error(self):
        user_answer = dedent("""
        def add(a, b):
            return add(3, 3)
        """)
        recursion_error_msg = ["Traceback", "call", "RuntimeError",
                                "maximum recursion depth exceeded"]
        get_evaluator = PythonCodeEvaluator(self.test_case_data, self.test,
                                            self.language, user_answer)
        result = get_evaluator.evaluate()
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(2, len(err))
        for msg in recursion_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_type_error(self):
        user_answer = dedent("""
        def add(a):
            return a + b
        """)
        type_error_msg = ["Traceback", "call", "TypeError", "exactly", "argument"]
        get_evaluator = PythonCodeEvaluator(self.test_case_data, self.test,
                                            self.language, user_answer)
        result = get_evaluator.evaluate()
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(2, len(err))
        for msg in type_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_value_error(self):
        user_answer = dedent("""
        def add(a, b):
            c = 'a'
            return int(a) + int(b) + int(c)
        """)
        value_error_msg = ["Traceback", "call", "ValueError", "invalid literal", "base"]
        get_evaluator = PythonCodeEvaluator(self.test_case_data, self.test,
                                            self.language, user_answer)
        result = get_evaluator.evaluate()
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(2, len(err))
        for msg in value_error_msg:
            self.assertIn(msg, result.get("error"))

if __name__ == '__main__':
    unittest.main()