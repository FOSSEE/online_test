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
            {"test_case": "bash_files/sample.sh,bash_files/sample.args"}
        ]
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path
        self.timeout_msg = ("Code took more than {0} seconds to run. "
            "You probably have an infinite loop in your"
            " code.").format(SERVER_TIMEOUT)
        self.file_paths = None
        self.hook_code = None

    def tearDown(self):
        os.remove('/tmp/test.txt')
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        user_answer = ("#!/bin/bash\n[[ $# -eq 2 ]]"
            " && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))"
        )
        get_class = BashCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths,
                    'hook_code': self.hook_code
                }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('error'), "Correct answer")

    def test_error(self):
        user_answer = ("#!/bin/bash\n[[ $# -eq 2 ]] "
            "&& echo $(( $1 - $2 )) && exit $(( $1 - $2 ))")
        get_class = BashCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths,
                    'hook_code': self.hook_code
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertTrue("Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = ("#!/bin/bash\nwhile [ 1 ] ;"
            " do echo "" > /dev/null ; done")
        get_class = BashCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths,
                    'hook_code': self.hook_code
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), self.timeout_msg)

    def test_file_based_assert(self):
        self.file_paths = [('/tmp/test.txt', False)]
        self.test_case_data = [
            {"test_case": "bash_files/sample1.sh,bash_files/sample1.args"}
        ]
        user_answer = ("#!/bin/bash\ncat $1")
        get_class = BashCodeEvaluator()
        kwargs = {'user_answer': user_answer,
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths,
                    'hook_code': self.hook_code
                }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

class BashStdioEvaluationTestCases(unittest.TestCase):
    def setUp(self):
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
        test_case_data = [{'expected_output': '11', 'expected_input': '5\n6'}]
        get_class = BashStdioEvaluator()
        kwargs = {"user_answer": user_answer,
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
                           'expected_input': '1,2,3\n4,5,6\n7,8,9'
                           }]
        get_class = BashStdioEvaluator()
        kwargs = {"user_answer": user_answer,
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
        test_case_data = [{'expected_output': '11', 'expected_input': '5\n6'}]
        get_class = BashStdioEvaluator()
        kwargs = {"user_answer": user_answer,
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
                           'expected_input': ''
                           }]
        get_class = BashStdioEvaluator()
        kwargs = {"user_answer": user_answer,
                  "test_case_data": test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEqual(result.get('error'), "Correct answer")
        self.assertTrue(result.get('success'))


class BashHookEvaluationTestCases(unittest.TestCase):

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
                              echo $((1+2))
                           """
                             )
        hook = dedent("""
                         def python_hook(user_answer, user_output):
                             if "3" in user_output and "echo" in user_answer:
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
        evaluator = BashStdioEvaluator(self.in_dir)
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertIn("Correct answer", result.get('error'))

    def test_incorrect_answer(self):

        # Given
        user_answer = dedent("""
                              echo $((1+3))
                           """
                             )
        hook = dedent("""
                         def python_hook(user_answer, user_output):
                             if "3" in user_output and "echo" in user_answer:
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
        evaluator = BashStdioEvaluator(self.in_dir)
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect answer", result.get('error'))

    def test_infinite_loop(self):

        # Given
        user_answer = ("#!/bin/bash\nwhile [ 1 ] ;"
                       " do echo "" > /dev/null ; done")
        hook = dedent("""
                       def python_hook(user_answer, user_output):
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
        evaluator = BashStdioEvaluator(self.in_dir)
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('error'), self.timeout_msg)

    def test_git_question(self):

        # Given
        user_answer = dedent("""
                              touch readme.txt
                              git init
                              git add readme.txt
                              echo first commit >> readme.txt
                              git commit -am "first commit"
                              """)

        hook = dedent("""
                        def python_hook(user_answer, user_output):
                            import re
                            with open("readme.txt") as f:
                                content = bool(any("first commit")\
                                          in lines for lines in f.readlines())

                            keywords = ["init", "commit", "add"]
                            ans_check = bool(all(words in user_answer for words in keywords))
                            git_init = bool("Initialized empty Git repository" in user_output)
                            commit = bool(re.search("create mode \d{1,9} readme.txt",
                                                     user_output))
                            if all([content, git_init, commit, ans_check]):
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
        evaluator = BashStdioEvaluator(self.in_dir)
        result = evaluator.evaluate(**kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertIn("Correct answer", result.get('error'))


if __name__ == '__main__':
    unittest.main()
