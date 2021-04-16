from __future__ import unicode_literals
import unittest
import os
import tempfile
import shutil
from textwrap import dedent

# Local import
from yaksh.grader import Grader
from yaksh.settings import SERVER_TIMEOUT


class EvaluatorBaseTest(unittest.TestCase):
    def assert_correct_output(self, expected_output, actual_output):
        actual_output_as_string = ''.join(actual_output)
        self.assertIn(expected_output, actual_output_as_string)


class PythonAssertionEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        self.tmp_file = os.path.join(tempfile.gettempdir(), "test.txt")
        with open(self.tmp_file, 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path
        self.test_case_data = [{"test_case_type": "standardtestcase",
                                "test_case": 'assert(add(1,2)==3)',
                                'weight': 0.0, 'hidden': True},
                               {"test_case_type": "standardtestcase",
                                "test_case": 'assert(add(-1,2)==1)',
                                'weight': 0.0, 'hidden': True},
                               {"test_case_type": "standardtestcase",
                                "test_case":  'assert(add(-1,-2)==-3)',
                                'weight': 0.0, 'hidden': True},
                               ]
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove(self.tmp_file)
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a + b"
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a - b"
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        given_test_case_list = [tc["test_case"] for tc in self.test_case_data]
        for error in result.get("error"):
            self.assertEqual(error['exception'], 'AssertionError')
            self.assertTrue(error['hidden'])
            self.assertEqual(
                error['message'],
                "Expected answer from the test case did not match the output"
                )
        error_testcase_list = [tc['test_case'] for tc in result.get('error')]
        self.assertEqual(error_testcase_list, given_test_case_list)

    def test_partial_incorrect_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn abs(a) + abs(b)"
        test_case_data = [{"test_case_type": "standardtestcase",
                           "test_case": 'assert(add(-1,2)==1)',
                           'weight': 1.0, 'hidden': False},
                          {"test_case_type": "standardtestcase",
                           "test_case":  'assert(add(-1,-2)==-3)',
                           'weight': 1.0, 'hidden': False},
                          {"test_case_type": "standardtestcase",
                           "test_case": 'assert(add(1,2)==3)',
                           'weight': 2.0, 'hidden': False}
                          ]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': True,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('weight'), 2.0)
        given_test_case_list = [tc["test_case"] for tc in self.test_case_data]
        given_test_case_list.remove('assert(add(1,2)==3)')
        for error in result.get("error"):
            self.assertEqual(error['exception'], 'AssertionError')
            self.assertFalse(error['hidden'])
            self.assertEqual(
                error['message'],
                "Expected answer from the test case did not match the output"
                )
        error_testcase_list = [tc['test_case'] for tc in result.get('error')]
        self.assertEqual(error_testcase_list, given_test_case_list)

    def test_infinite_loop(self):
        # Given
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assert_correct_output(self.timeout_msg,
                                   result.get("error")[0]["message"]
                                   )

    def test_syntax_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b);
            return a + b
        """)
        syntax_error_msg = ["Traceback",
                            "call",
                            "File",
                            "line",
                            "<string>",
                            "SyntaxError",
                            "invalid syntax"
                            ]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        err = result.get("error")[0]['traceback']
        # Then
        self.assertFalse(result.get("success"))
        for msg in syntax_error_msg:
            self.assert_correct_output(msg, err)

    def test_indent_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b):
        return a + b
        """)
        indent_error_msg = ["Traceback", "call",
                            "File",
                            "line",
                            "<string>",
                            "IndentationError",
                            "indented block"
                            ]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        err = result.get("error")[0]["traceback"].splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(5, len(err))
        for msg in indent_error_msg:
            self.assert_correct_output(
                msg, result.get("error")[0]['traceback']
            )

    def test_name_error(self):
        # Given
        user_answer = ""
        name_error_msg = ["Traceback",
                          "call",
                          "NameError",
                          "name",
                          "defined"
                          ]

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        err = result.get("error")[0]["traceback"]
        for msg in name_error_msg:
            self.assertIn(msg, err)

    def test_recursion_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b):
            return add(3, 3)
        """)
        recursion_error_msg = "maximum recursion depth exceeded"
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        err = result.get("error")[0]['message']

        # Then
        self.assertFalse(result.get("success"))
        self.assert_correct_output(recursion_error_msg, err)

    def test_type_error(self):
        # Given
        user_answer = dedent("""
        def add(a):
            return a + b
        """)
        type_error_msg = ["Traceback",
                          "call",
                          "TypeError",
                          "argument"
                          ]

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        err = result.get("error")[0]['traceback']

        # Then
        self.assertFalse(result.get("success"))
        for msg in type_error_msg:
            self.assert_correct_output(msg, err)

    def test_value_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b):
            c = 'a'
            return int(a) + int(b) + int(c)
        """)
        value_error_msg = ["Traceback",
                           "call",
                           "ValueError",
                           "invalid literal",
                           "base"
                           ]

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get("error")

        # Then
        self.assertFalse(result.get("success"))
        for msg in value_error_msg:
            self.assert_correct_output(msg, errors[0]['traceback'])
        for index, error in enumerate(errors):
            self.assertEqual(error['test_case'],
                             self.test_case_data[index]['test_case'])

    def test_file_based_assert(self):
        # Given
        self.test_case_data = [{"test_case_type": "standardtestcase",
                                "test_case": "assert(ans()=='2')",
                                "weight": 0.0}
                               ]
        self.file_paths = [(self.tmp_file, False)]
        user_answer = dedent("""
            def ans():
                with open("test.txt") as f:
                    return f.read()[0]
            """)

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_single_testcase_error(self):
        """ Tests the user answer with just an incorrect test case """

        # Given
        user_answer = "def palindrome(a):\n\treturn a == a[::-1]"
        test_case_data = [{"test_case_type": "standardtestcase",
                           "test_case": 's="abbb"\nasert palindrome(s)==False',
                           "weight": 0.0
                           }
                          ]
        syntax_error_msg = ["Traceback",
                            "call",
                            "SyntaxError",
                            "invalid syntax"
                            ]

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        err = result.get("error")[0]['traceback']

        # Then
        self.assertFalse(result.get("success"))
        for msg in syntax_error_msg:
            self.assert_correct_output(msg, err)

    def test_multiple_testcase_error(self):
        """ Tests the user answer with an correct test case
         first and then with an incorrect test case """
        # Given
        user_answer = "def palindrome(a):\n\treturn a == a[::-1]"
        test_case_data = [{"test_case_type": "standardtestcase",
                           "test_case": 'assert(palindrome("abba")==True)',
                           "weight": 0.0},
                          {"test_case_type": "standardtestcase",
                           "test_case": 's="abbb"\n'
                                        'assert palindrome(S)==False',
                           "weight": 0.0}
                          ]
        name_error_msg = ["Traceback",
                          "call",
                          "NameError",
                          "name 'S' is not defined"
                          ]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        err = result.get("error")[0]['traceback']

        # Then
        self.assertFalse(result.get("success"))
        for msg in name_error_msg:
            self.assertIn(msg, err)

    def test_unicode_literal_bug(self):
        # Given
        user_answer = dedent("""\
                             def strchar(s):
                                a = "should be a string"
                                return type(a)
                            """)
        test_case_data = [{"test_case_type": "standardtestcase",
                           "test_case": 'assert(strchar("hello")==str)',
                           "weight": 0.0}]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }
        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get("success"))

    def test_incorrect_answer_with_nose_assert(self):
        user_answer = dedent("""\
                             def add(a, b):
                                return a - b
                            """)
        test_case_data = [{"test_case_type": "standardtestcase",
                           "test_case": 'assert_equal(add(1, 2), 3)',
                           "weight": 0.0}]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }
        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get("success"))
        error = result.get("error")[0]
        self.assertEqual(error['exception'], 'AssertionError')
        self.assertEqual(error['message'], '-1 != 3')


class PythonStdIOEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        self.tmp_file = os.path.join(tempfile.gettempdir(), "test.txt")
        with open(self.tmp_file, 'wb') as f:
            f.write('2'.encode('ascii'))
        self.file_paths = None
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path

    def teardown(self):
        os.remove(self.tmp_file)
        shutil.rmtree(self.in_dir)

    def test_correct_answer_integer(self):
        # Given
        test_case_data = [{"test_case_type": "stdiobasedtestcase",
                                "expected_input": "1\n2",
                                "expected_output": "3",
                                "weight": 0.0
                                }]
        user_answer = dedent("""
                                a = int(input())
                                b = int(input())
                                print(a+b)
                             """
                             )
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_correct_answer_list(self):
        # Given
        test_case_data = [{"test_case_type": "stdiobasedtestcase",
                                "expected_input": "1,2,3\n5,6,7",
                                "expected_output": "[1, 2, 3, 5, 6, 7]",
                                "weight": 0.0
                                }]
        user_answer = dedent("""
                                input_a = input()
                                input_b = input()
                                a = [int(i) for i in input_a.split(',')]
                                b = [int(i) for i in input_b.split(',')]
                                print(a+b)
                             """
                             )

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_correct_answer_string(self):
        # Given
        test_case_data = [{
            "test_case_type": "stdiobasedtestcase",
            "expected_input": ("the quick brown fox jumps over "
                               "the lazy dog\nthe"),
            "expected_output": "2",
            "weight": 0.0
            }]
        user_answer = dedent("""
                                a = input()
                                b = input()
                                print(a.count(b))
                             """
                             )

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer_integer(self):
        # Given
        test_case_data = [{"test_case_type": "stdiobasedtestcase",
                                "expected_input": "1\n2",
                                "expected_output": "3",
                                "weight": 0.0, 'hidden': True
                                }]
        user_answer = dedent("""
                                a = int(input())
                                b = int(input())
                                print(a-b)
                             """
                             )
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertTrue(result.get('error')[0].get('hidden'))
        self.assert_correct_output(
            "Incorrect Answer: Line number(s) 1 did not match.",
            result.get('error')[0].get('error_msg')
        )

    def test_file_based_answer(self):
        # Given
        test_case_data = [{"test_case_type": "stdiobasedtestcase",
                                "expected_input": "",
                                "expected_output": "2",
                                "weight": 0.0
                                }]
        self.file_paths = [(self.tmp_file, False)]

        user_answer = dedent("""
                            with open("test.txt") as f:
                                a = f.read()
                                print(a[0])
                             """
                             )
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_infinite_loop(self):
        # Given
        self.test_case_data = [{
            "test_case_type": "stdiobasedtestcase",
            "expected_input": "1\n2",
            "expected_output": "3",
            "weight": 0.0
            }]
        timeout_msg = ("Code took more than {0} seconds to run. "
                       "You probably have an infinite loop in"
                       " your code.").format(SERVER_TIMEOUT)
        user_answer = "while True:\n\tpass"

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': self.test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assert_correct_output(timeout_msg,
                                   result.get("error")[0]["message"]
                                   )
        self.assertFalse(result.get('success'))

    def test_unicode_literal_bug(self):
        # Given
        user_answer = dedent("""\
                             a = "this should be a string."
                             print(type(a).__name__)
                            """)
        test_case_data = [{"test_case_type": "stdiobasedtestcase",
                           "expected_input": "",
                           "expected_output": "str",
                           "weight": 0.0
                           }]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }
        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        # Then
        self.assertTrue(result.get("success"))

    def test_get_error_lineno(self):
        user_answer = dedent("""\
                             print(1/0)
                            """)
        test_case_data = [{"test_case_type": "stdiobasedtestcase",
                           "expected_input": "",
                           "expected_output": "1",
                           "weight": 0.0
                           }]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }
        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        # Then
        self.assertFalse(result.get("success"))
        error = result.get("error")[0]
        self.assertEqual(error['line_no'], 1)
        self.assertEqual(error['exception'], "ZeroDivisionError")


class PythonHookEvaluationTestCases(EvaluatorBaseTest):

    def setUp(self):
        self.tmp_file = os.path.join(tempfile.gettempdir(), "test.txt")
        with open(self.tmp_file, 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove(self.tmp_file)
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a + b"
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                exec(user_answer, globals())
                                if add(1,2) == 3:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                           )

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code, "weight": 1.0
                           }]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': True,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a - b"
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                exec(user_answer, globals())
                                if add(1,2) == 3:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                           )

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code, "weight": 1.0,
                           "hidden": True
                           }]

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertTrue(result.get('error')[0]['hidden'])
        self.assert_correct_output('Incorrect Answer',
                                   result.get('error')[0]['message'])

    def test_assert_with_hook(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a + b"
        assert_test_case = "assert add(1,2) == 3"
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                if "return a + b" in user_answer:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                           )

        test_case_data = [{"test_case_type": "standardtestcase",
                           "test_case": assert_test_case, 'weight': 1.0},
                          {"test_case_type": "hooktestcase",
                           "hook_code": hook_code, 'weight': 1.0},
                          ]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': True,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get("weight"), 2.0)

    def test_multiple_hooks(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a + b"
        hook_code_1 = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                if "return a + b" in user_answer:
                                    success, err, mark_fraction = True, "", 0.5
                                return success, err, mark_fraction
                            """
                             )
        hook_code_2 = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                exec(user_answer, globals())
                                if add(1,2) == 3:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                             )

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code_1, 'weight': 1.0},
                          {"test_case_type": "hooktestcase",
                           "hook_code": hook_code_2, 'weight': 1.0},
                          ]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': True,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get("weight"), 1.5)

    def test_infinite_loop(self):
        # Given
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                exec(user_answer, globals())
                                if add(1,2) == 3:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                           )

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code, "weight": 1.0
                           }]

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assert_correct_output(self.timeout_msg,
                                   result.get("error")[0]["message"]
                                   )

    def test_assignment_upload(self):
        # Given
        user_answer = "Assignment Upload"
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                with open("test.txt") as f:
                                    data = f.read()
                                if data == '2':
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                           )

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code, "weight": 1.0
                           }]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'assign_files': [(self.tmp_file, False)],
                  'partial_grading': False,
                  'language': 'python'},
                  'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))


if __name__ == '__main__':
    unittest.main()
