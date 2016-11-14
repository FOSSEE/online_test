from __future__ import unicode_literals
import unittest
import os
import tempfile
import shutil
from textwrap import dedent

# Local import
from yaksh.python_assertion_evaluator import PythonAssertionEvaluator
from yaksh.python_stdio_evaluator import PythonStdioEvaluator
from yaksh.settings import SERVER_TIMEOUT


class PythonAssertionEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        with open('/tmp/test.txt', 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path
        self.test_case_data = [{"test_case": 'assert(add(1,2)==3)'},
                               {"test_case": 'assert(add(-1,2)==1)'},
                               {"test_case":  'assert(add(-1,-2)==-3)'},
                               ]
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

        self.hook_code = None

    def tearDown(self):
        os.remove('/tmp/test.txt')
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a + b"
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('error'), "Correct answer")

    def test_incorrect_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a - b"
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'),
                         "AssertionError  in: assert(add(1,2)==3)"
                         )

    def test_infinite_loop(self):
        # Given
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'), self.timeout_msg)

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
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)
        err = result.get("error").splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(5, len(err))
        for msg in syntax_error_msg:
            self.assertIn(msg, result.get("error"))

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
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)
        err = result.get("error").splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(5, len(err))
        for msg in indent_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_name_error(self):
        # Given
        user_answer = ""
        name_error_msg = ["Traceback",
                          "call",
                          "NameError",
                          "name",
                          "defined"
                          ]
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)
        err = result.get("error").splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(3, len(err))
        for msg in name_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_recursion_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b):
            return add(3, 3)
        """)
        recursion_error_msg = ["Traceback",
                               "call",
                               "maximum recursion depth exceeded"
                               ]
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)
        err = result.get("error").splitlines()

        # Then
        self.assertFalse(result.get("success"))
        for msg in recursion_error_msg:
            self.assertIn(msg, result.get("error"))

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
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)
        err = result.get("error").splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(3, len(err))
        for msg in type_error_msg:
            self.assertIn(msg, result.get("error"))

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
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)
        err = result.get("error").splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(4, len(err))
        for msg in value_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_file_based_assert(self):
        # Given
        self.test_case_data = [{"test_case": "assert(ans()=='2')"}]
        self.file_paths = [('/tmp/test.txt', False)]
        user_answer = dedent("""
            def ans():
                with open("test.txt") as f:
                    return f.read()[0]
            """)
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertEqual(result.get('error'), "Correct answer")
        self.assertTrue(result.get('success'))

    def test_single_testcase_error(self):
        # Given
        """ Tests the user answer with just an incorrect test case """

        user_answer = "def palindrome(a):\n\treturn a == a[::-1]"
        test_case_data = [{"test_case": 's="abbb"\nasert palindrome(s)==False'}
                          ]
        syntax_error_msg = ["Traceback",
                            "call",
                            "File",
                            "line",
                            "<string>",
                            "SyntaxError",
                            "invalid syntax"
                            ]
        kwargs = {'user_answer': user_answer,
                  'test_case_data': test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)
        err = result.get("error").splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(5, len(err))
        for msg in syntax_error_msg:
            self.assertIn(msg, result.get("error"))


    def test_multiple_testcase_error(self):
        """ Tests the user answer with an correct test case
         first and then with an incorrect test case """
        # Given
        user_answer = "def palindrome(a):\n\treturn a == a[::-1]"
        test_case_data = [{"test_case": 'assert(palindrome("abba")==True)'},
                          {"test_case": 's="abbb"\nassert palindrome(S)==False'}
                          ]
        name_error_msg = ["Traceback",
                          "call",
                          "File",
                          "line",
                          "<string>",
                          "NameError",
                          "name 'S' is not defined"
                          ]
        kwargs = {'user_answer': user_answer,
                  'test_case_data': test_case_data,
                  'file_paths': self.file_paths,
                  'hook_code': self.hook_code
                  }

        # When
        evaluator = PythonAssertionEvaluator()
        result = evaluator.evaluate(**kwargs)
        err = result.get("error").splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(3, len(err))
        for msg in name_error_msg:
            self.assertIn(msg, result.get("error"))


class PythonStdIOEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        with open('/tmp/test.txt', 'wb') as f:
            f.write('2'.encode('ascii'))
        self.file_paths = None

    def test_correct_answer_integer(self):
        # Given
        self.test_case_data = [{"expected_input": "1\n2",
                                "expected_output": "3"
                                }]
        user_answer = dedent("""
                                a = int(input())
                                b = int(input())
                                print(a+b)
                             """
                             )
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }

        # When
        evaluator = PythonStdioEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertIn("Correct answer", result.get('error'))

    def test_correct_answer_list(self):
        # Given
        self.test_case_data = [{"expected_input": "1,2,3\n5,6,7",
                                "expected_output": "[1, 2, 3, 5, 6, 7]"
                                }]
        user_answer = dedent("""
                                from six.moves import input
                                input_a = input()
                                input_b = input()
                                a = [int(i) for i in input_a.split(',')]
                                b = [int(i) for i in input_b.split(',')]
                                print(a+b)
                             """
                             )
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }

        # When
        evaluator = PythonStdioEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertIn("Correct answer", result.get('error'))

    def test_correct_answer_string(self):
        # Given
        self.test_case_data = [{"expected_input": ("the quick brown fox jumps over the lazy dog\nthe"),
                                "expected_output": "2"
                                }]
        user_answer = dedent("""
                                from six.moves import input
                                a = str(input())
                                b = str(input())
                                print(a.count(b))
                             """
                             )
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }

        # When
        evaluator = PythonStdioEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertIn("Correct answer", result.get('error'))

    def test_incorrect_answer_integer(self):
        # Given
        self.test_case_data = [{"expected_input": "1\n2",
                                "expected_output": "3"
                                }]
        user_answer = dedent("""
                                a = int(input())
                                b = int(input())
                                print(a-b)
                             """
                             )
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  }

        # When
        evaluator = PythonStdioEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect answer", result.get('error'))

    def test_file_based_answer(self):
        # Given
        self.test_case_data = [{"expected_input": "", "expected_output": "2"}]
        self.file_paths = [('/tmp/test.txt', False)]

        user_answer = dedent("""
                            with open("test.txt") as f:
                                a = f.read()
                                print(a[0])
                             """
                             )
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths
                  }

        # When
        evaluator = PythonStdioEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertEqual(result.get('error'), "Correct answer")
        self.assertTrue(result.get('success'))

    def test_infinite_loop(self):
        # Given
        test_case_data = [{"expected_input": "1\n2",
                                "expected_output": "3"
                                }]
        timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        user_answer = "while True:\n\tpass"
        kwargs = {'user_answer': user_answer,
                  'test_case_data': test_case_data
                  }
        # When
        evaluator = PythonStdioEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertEqual(result.get('error'), timeout_msg)
        self.assertFalse(result.get('success'))


class PythonHookEvaluationTestCases(unittest.TestCase):

    def setUp(self):
        with open('/tmp/test.txt', 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path
        self.test_case_data = [{"expected_input": None,
                                "expected_output": None
                                }
                               ]
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove('/tmp/test.txt')
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):

        # Given
        user_answer = dedent("""
                              print (1+2)
                           """
                             )
        hook = dedent("""
                        def check_answer(user_answer, user_output):
                            if int(user_output) == 3 and "print" in user_answer:
                                success = True
                                err = "Correct answer"
                            else:
                                success = False
                                err = "Incorrect answer"
                            return success, err
                       """
                      )
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'hook_code': hook}
        # When
        evaluator = PythonStdioEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertIn("Correct answer", result.get('error'))

    def test_incorrect_answer(self):

        # Given
        user_answer = dedent("""
                              print (1+3)
                           """
                             )
        hook = dedent("""
                       def check_answer(user_answer, user_output):
                           if int(user_output) == 3:
                               success = True
                               err = "Correct answer"
                           else:
                               success = False
                               err = '''Incorrect answer.
                                        Expected output - {0},
                                        Your output {1}'''\
                                         .format(3,user_output)
                           return success, err
                       """
                      )
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'hook_code': hook}
        # When
        evaluator = PythonStdioEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect answer", result.get('error'))

    def test_infinite_loop(self):

        # Given
        user_answer = dedent("""
                              while True:
                                print ("Loop")
                           """
                             )
        hook = dedent("""
                       def check_answer(user_answer, user_output):
                           if int(user_output) == 3:
                               success = True
                               err = "Correct answer"
                           else:
                               success = False
                               err = '''Incorrect answer.
                                        Expected output - {0},
                                        Your output {1}'''\
                                         .format(3,user_output)
                           return success, err
                       """
                      )
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'hook_code': hook}
        # When
        evaluator = PythonStdioEvaluator()
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'), self.timeout_msg)


if __name__ == '__main__':
    unittest.main()
