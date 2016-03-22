import unittest
import os
from yaksh.python_assertion_evaluator import PythonAssertionEvaluator
from yaksh.python_stdout_evaluator import PythonStdoutEvaluator
from yaksh.settings import SERVER_TIMEOUT

class PythonAssertionEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.test_case_data = ['assert(add(1,2)==3)']
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        # {u'user_answer': u'def adder(a,b):\r\n    return a', u'test_case_data': [u'assert(adder(1,2)==3)']}
        user_answer = "def add(a,b):\n\treturn a + b"
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('error'), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "def add(a,b):\n\treturn a - b"
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'), "AssertionError  in: assert(add(1,2)==3)")

    def test_infinite_loop(self):
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"
        get_class = PythonAssertionEvaluator()
        kwargs = {'user_answer': user_answer,
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'), self.timeout_msg)

class PythonStdoutEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.output = ['0 1 1 2 3']
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        # user_answer = "a = 'Hello'\nb = 'World'\nprint '{0} {1}'.format(a, b)"
        user_answer = "a,b=0,1\nfor i in range(5):\n\tprint a,\n\ta,b=b,a+b"
        get_class = PythonStdoutEvaluator()
        kwargs = {'user_answer': user_answer,
                    'test_case_data': self.output
                }
        result = get_class.evaluate(**kwargs)
        self.assertEqual(result.get('error'), "Correct answer")
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        user_answer = "a,b=0,1\nfor i in range(5):\n\tprint b,\n\ta,b=b,a+b"
        get_class = PythonStdoutEvaluator()
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.output
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'), "Incorrect Answer")

    def test_direct_printed_answer(self):
        user_answer = "print '0 1 1 2 3'"
        error_msg = "Incorrect Answer: Please avoid printing the expected output directly"
        get_class = PythonStdoutEvaluator()
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.output
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'), error_msg)

    def test_infinite_loop(self):
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"
        get_class = PythonStdoutEvaluator()
        kwargs = {'user_answer': user_answer,
                    'test_case_data': self.output
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'), 'Incorrect Answer')


if __name__ == '__main__':
    unittest.main()
