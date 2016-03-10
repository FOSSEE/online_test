import unittest
import os
from yaksh.python_code_evaluator import PythonCodeEvaluator
from yaksh.settings import SERVER_TIMEOUT
import textwrap

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
        user_answer = textwrap.dedent("""
                                    def add(a, b):
                                        return a + b
                                    """)
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = textwrap.dedent("""
                                    def add(a, b):
                                        return a - b
                                    """)
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), "AssertionError  in: assert add(3, 2) == 5")

    def test_infinite_loop(self):
        user_answer = textwrap.dedent("""
                                    def add(a, b):
                                        while True:
                                            pass
                                    """)
        timeout_msg = ("Code took more than {0} seconds to run. "
                       "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), timeout_msg)

    def test_syntax_error(self):
        # Do not touch any error messages as it can fail test case
        user_answer = textwrap.dedent("""
                                    def add(a, b);
                                        return a + b
                                    """)
        syntax_error_msg = textwrap.dedent("""\
                                        Traceback (most recent call last):
                                          File "<string>", line 2
                                            def add(a, b);
                                                         ^
                                        SyntaxError: invalid syntax\n""")
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), syntax_error_msg)

    def test_indent_error(self):
        user_answer = textwrap.dedent("""
                                    def add(a, b):
                                    return a + b
                                    """)
        indent_error_msg = textwrap.dedent("""\
                                        Traceback (most recent call last):
                                          File "<string>", line 3
                                            return a + b
                                                 ^
                                        IndentationError: expected an indented block
                                        """)
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), indent_error_msg)

    def test_name_error(self):
        user_answer = ""
        name_error_msg = textwrap.dedent("""\
                                        Traceback (most recent call last):
                                        NameError: name 'add' is not defined
                                        """)
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), name_error_msg)

    def test_recursion_error(self):
        user_answer = textwrap.dedent("""
                                    def add(a, b):
                                        return add(3, 3)
                                    """)
        recursion_error_msg = textwrap.dedent("""\
                                            Traceback (most recent call last):
                                            RuntimeError: maximum recursion depth exceeded
                                            """)
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), recursion_error_msg)

    def test_type_error(self):
        user_answer = textwrap.dedent("""
                                    def add(a):
                                        return a + b
                                    """)
        type_error_msg = textwrap.dedent("""\
                                        Traceback (most recent call last):
                                        TypeError: add() takes exactly 1 argument (2 given)
                                        """)
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), type_error_msg)

    def test_value_error(self):
        user_answer = textwrap.dedent("""
                                    def add(a, b):
                                        c = 'a'
                                        return int(a) + int(b) + int(c)
                                    """)
        value_error_msg = textwrap.dedent("""\
                                        Traceback (most recent call last):
                                        ValueError: invalid literal for int() with base 10: 'a'
                                        """)
        evaluator = PythonCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = evaluator.evaluate()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), value_error_msg)

if __name__ == '__main__':
    unittest.main()
