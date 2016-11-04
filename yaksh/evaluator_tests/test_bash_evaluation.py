from __future__ import unicode_literals
import unittest
import os
import shutil
import tempfile
from yaksh.bash_code_evaluator import BashCodeEvaluator
from yaksh.bash_stdio_evaluator import BashStdioEvaluator
from yaksh.settings import SERVER_TIMEOUT
from textwrap import dedent


class BashAssertionEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        with open('/tmp/test.txt', 'wb') as f:
            f.write('2'.encode('ascii'))
        self.test_case_data = [
            {"test_case": "bash_files/sample.sh,bash_files/sample.args",
                "marks": 0.0
            }
        ]
        self.in_dir = tempfile.mkdtemp()
        self.timeout_msg = ("Code took more than {0} seconds to run. "
            "You probably have an infinite loop in your"
            " code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove('/tmp/test.txt')
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        user_answer = ("#!/bin/bash\n[[ $# -eq 2 ]]"
            " && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))"
        )
        get_class = BashCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer,
                    'partial_grading': True,
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('error'), "Correct answer")

    def test_error(self):
        user_answer = ("#!/bin/bash\n[[ $# -eq 2 ]] "
            "&& echo $(( $1 - $2 )) && exit $(( $1 - $2 ))")
        get_class = BashCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer,
                    'partial_grading': True,
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertTrue("Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = ("#!/bin/bash\nwhile [ 1 ] ;"
            " do echo "" > /dev/null ; done")
        get_class = BashCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer,
                    'partial_grading': True,
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), self.timeout_msg)

    def test_file_based_assert(self):
        self.file_paths = [('/tmp/test.txt', False)]
        self.test_case_data = [
            {"test_case": "bash_files/sample1.sh,bash_files/sample1.args",
                "marks": 0.0
            }
        ]
        user_answer = ("#!/bin/bash\ncat $1")
        get_class = BashCodeEvaluator()
        kwargs = {'user_answer': user_answer,
                    'partial_grading': True,
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

class BashStdioEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.in_dir = tempfile.mkdtemp()
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your"
                            " code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        user_answer = dedent(""" #!/bin/bash
                             read A
                             read B
                             echo -n `expr $A + $B`
                             """
                             )
        test_case_data = [{'expected_output': '11',
            'expected_input': '5\n6',
            'marks': 0.0
            }]
        get_class = BashStdioEvaluator()
        kwargs = {"user_answer": user_answer,
                    "partial_grading": True,
                    "test_case_data": test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertEqual(result.get('error'), "Correct answer")
        self.assertTrue(result.get('success'))

    def test_array_input(self):
        user_answer = dedent(""" readarray arr;
                                 COUNTER=0
                                 while [  $COUNTER -lt 3 ]; do
                                     echo -n "${arr[$COUNTER]}"
                                     let COUNTER=COUNTER+1 
                                 done
                            """
                             )
        test_case_data = [{'expected_output': '1 2 3\n4 5 6\n7 8 9\n',
                           'expected_input': '1,2,3\n4,5,6\n7,8,9',
                           'marks': 0.0
                           }]
        get_class = BashStdioEvaluator()
        kwargs = {"user_answer": user_answer,
                    "partial_grading": True,
                    "test_case_data": test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertEqual(result.get('error'), "Correct answer")
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        user_answer = dedent(""" #!/bin/bash
                             read A
                             read B
                             echo -n `expr $A - $B`
                             """
                             )
        test_case_data = [{'expected_output': '11',
            'expected_input': '5\n6',
            'marks': 0.0
            }]
        get_class = BashStdioEvaluator()
        kwargs = {"user_answer": user_answer,
                    "partial_grading": True,
                    "test_case_data": test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertIn("Incorrect", result.get('error'))
        self.assertFalse(result.get('success'))

    def test_stdout_only(self):
        user_answer = dedent(""" #!/bin/bash
                             A=6
                             B=4
                             echo -n `expr $A + $B`
                             """
                             )
        test_case_data = [{'expected_output': '10',
                           'expected_input': '',
                           'marks': 0.0
                           }]
        get_class = BashStdioEvaluator()
        kwargs = {"user_answer": user_answer,
                    "partial_grading": True,
                    "test_case_data": test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertEqual(result.get('error'), "Correct answer")
        self.assertTrue(result.get('success'))

if __name__ == '__main__':
    unittest.main()
