import unittest
import os
from yaksh.python_assertion_evaluator import PythonAssertionEvaluator
from yaksh.python_stdio_evaluator import PythonStdioEvaluator
from yaksh.settings import SERVER_TIMEOUT
from textwrap import dedent


class PythonAssertionEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.test_case_data = [{"test_case": 'assert(add(1,2)==3)'},
            {"test_case": 'assert(add(-1,2)==1)'},
            {"test_case":  'assert(add(-1,-2)==-3)'},
        ]
        self.timeout_msg = ("Code took more than {0} seconds to run. "
            "You probably have an infinite loop in"
            " your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def test_correct_answer(self):
        user_answer = "def add(a,b):\n\treturn a + b"
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths
                  }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('error'), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "def add(a,b):\n\treturn a - b"
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths
                  }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'),
            "AssertionError  in: assert(add(1,2)==3)"
        )

    def test_infinite_loop(self):
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
            'test_case_data': self.test_case_data,
            'file_paths': self.file_paths
        }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'), self.timeout_msg)

    def test_syntax_error(self):
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
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
            'test_case_data': self.test_case_data,
            'file_paths': self.file_paths
        }
        result = get_class.evaluate(**kwargs)
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
        indent_error_msg = ["Traceback", "call", 
            "File",
            "line",
            "<string>",
            "IndentationError",
            "indented block"
        ]
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
            'test_case_data': self.test_case_data,
            'file_paths': self.file_paths
        }
        result = get_class.evaluate(**kwargs)
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(5, len(err))
        for msg in indent_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_name_error(self):
        user_answer = ""
        name_error_msg = ["Traceback", 
            "call",
            "NameError",
            "name",
            "defined"
        ]
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
            'test_case_data': self.test_case_data,
            'file_paths': self.file_paths
        }
        result = get_class.evaluate(**kwargs)
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(3, len(err))
        for msg in name_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_recursion_error(self):
        user_answer = dedent("""
        def add(a, b):
            return add(3, 3)
        """)
        recursion_error_msg = ["Traceback",
            "call", 
            "RuntimeError",
            "maximum recursion depth exceeded"
        ]
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
            'test_case_data': self.test_case_data,
            'file_paths': self.file_paths
        }
        result = get_class.evaluate(**kwargs)
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(969, len(err))
        for msg in recursion_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_type_error(self):
        user_answer = dedent("""
        def add(a):
            return a + b
        """)
        type_error_msg = ["Traceback", 
            "call", 
            "TypeError",
            "exactly",
            "argument"
        ]
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
            'test_case_data': self.test_case_data,
            'file_paths': self.file_paths
        }
        result = get_class.evaluate(**kwargs)
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(3, len(err))
        for msg in type_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_value_error(self):
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
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths
                  }
        result = get_class.evaluate(**kwargs)
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(4, len(err))
        for msg in value_error_msg:
            self.assertIn(msg, result.get("error"))

    def test_file_based_assert(self):
        self.test_case_data = [{"test_case": "assert(ans()=='2')"}]
        self.file_paths = [(os.getcwd()+"/yaksh/test.txt", False)]
        user_answer = dedent("""
            def ans():
                with open("test.txt") as f:
                    return f.read()[0]
            """)
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
            'test_case_data': self.test_case_data,
            'file_paths': self.file_paths
        }
        result = get_class.evaluate(**kwargs)
        self.assertEqual(result.get('error'), "Correct answer")
        self.assertTrue(result.get('success'))

    def test_single_testcase_error(self):
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
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': test_case_data,
                  'file_paths': self.file_paths
                  }
        result = get_class.evaluate(**kwargs)
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(5, len(err))
        for msg in syntax_error_msg:
            self.assertIn(msg, result.get("error"))


    def test_multiple_testcase_error(self):
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
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': test_case_data,
                  'file_paths': self.file_paths
                  }
        result = get_class.evaluate(**kwargs)
        err = result.get("error").splitlines()
        self.assertFalse(result.get("success"))
        self.assertEqual(3, len(err))
        for msg in name_error_msg:
            self.assertIn(msg, result.get("error"))


class PythonStdoutEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.test_case_data = [{"expected_input": None,
                                "expected_output": "0 1 1 2 3"
                                }]

        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop"
                            " in your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def test_correct_answer(self):
        user_answer = "a,b=0,1\nfor i in range(5):\n\tprint a,\n\ta,b=b,a+b"
        get_class = PythonStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEqual(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        user_answer = "a,b=0,1\nfor i in range(5):\n\tprint b,\n\ta,b=b,a+b"
        get_class = PythonStdioEvaluator()
        kwargs = {'user_answer': user_answer, 
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths
                  }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect Answer", result.get('error'))

    def test_infinite_loop(self):
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass\nadd(1,2)"
        get_class = PythonStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEqual(result.get('error'), self.timeout_msg)
        self.assertFalse(result.get('success'))


class PythonStdIOEvaluator(unittest.TestCase):

    def setUp(self):
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop"
                            " in your code.").format(SERVER_TIMEOUT)

    def test_add_two_integers_correct(self):
        self.test_case_data = [{"expected_input": "1\n2",
                                "expected_output": "3"
                                }]
        user_answer = dedent("""
                                a = int(raw_input())
                                b = int(raw_input())
                                print a+b
                             """
                             )

        get_class = PythonStdioEvaluator()

        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertIn("Correct Answer", result.get('error'))

    def test_add_two_lists(self):
        self.test_case_data = [{"expected_input": "[1,2,3]\n[5,6,7]",
                                "expected_output": "[1, 2, 3, 5, 6, 7]"
                                }]
        user_answer = dedent("""
                                from ast import literal_eval
                                a = literal_eval(raw_input())
                                b = literal_eval(raw_input())
                                print a+b
                             """
                             )

        get_class = PythonStdioEvaluator()

        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertIn("Correct Answer", result.get('error'))

    def test_find_string_in_sentence(self):
        self.test_case_data = [{"expected_input": """the quick brown fox jumps\
                                                     over the lazy dog\nthe""",
                                "expected_output": "2"
                                }]
        user_answer = dedent("""
                                a = raw_input()
                                b = raw_input()
                                print (a.count(b))
                             """
                             )

        get_class = PythonStdioEvaluator()

        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertIn("Correct Answer", result.get('error'))

    def test_add_two_integers_incorrect(self):
        self.test_case_data = [{"expected_input": "1\n2",
                                "expected_output": "3"
                                }]
        user_answer = dedent("""
                                a = int(raw_input())
                                b = int(raw_input())
                                print a-b
                             """
                             )

        get_class = PythonStdioEvaluator()

        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect Answer", result.get('error'))

    def test_file_based_answer(self):
        self.test_case_data = [{"expected_input": "", "expected_output": "2"}]
        self.file_paths = [(os.getcwd()+"/yaksh/test.txt", False)]

        user_answer = dedent("""
                            with open("test.txt") as f:
                                a = f.read()
                                print a[0]
                             """
                             )
        get_class = PythonStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEqual(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

if __name__ == '__main__':
    unittest.main()
