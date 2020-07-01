from __future__ import unicode_literals
import unittest
import os
import shutil
import tempfile
from psutil import Process
# Local Imports
from yaksh.grader import Grader
from yaksh.evaluator_tests.test_python_evaluation import EvaluatorBaseTest
from yaksh.settings import SERVER_TIMEOUT
from textwrap import dedent


class BashAssertionEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        self.f_path = os.path.join(tempfile.gettempdir(), "test.txt")
        with open(self.f_path, 'wb') as f:
            f.write('2'.encode('ascii'))
        self.tc_data = dedent("""
            #!/bin/bash
            [[ $# -eq 2 ]] && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))
            """)
        self.tc_data_args = "1 2\n2 1"
        self.test_case_data = [
            {"test_case": self.tc_data,
             "test_case_args": self.tc_data_args,
             "test_case_type": "standardtestcase",
             "weight": 0.0, "hidden": False
             }
        ]
        self.in_dir = tempfile.mkdtemp()
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your"
                            " code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove(self.f_path)
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = ("#!/bin/bash\n[[ $# -eq 2 ]]"
                       " && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))"
                       )
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'bash'
                  }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_correct_answer_without_test_case_args(self):
        # Given
        user_answer = "echo 'hello'"
        tc_data = "echo 'hello'"
        self.test_case_data = [
            {"test_case": tc_data,
             "test_case_args": "",
             "test_case_type": "standardtestcase",
             "weight": 0.0,
             "hidden": True
             }
        ]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'bash'
                  }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer_without_test_case_args(self):
        # Given
        user_answer = "echo 'hello'"
        tc_data = "echo 'hello world'"
        self.test_case_data = [
            {"test_case": tc_data,
             "test_case_args": "",
             "test_case_type": "standardtestcase",
             "weight": 0.0
             }
        ]
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'bash'
                  }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))

    def test_error(self):
        # Given
        user_answer = ("#!/bin/bash\n[[ $# -eq 2 ]] "
                       "&& echo $(( $1 - $2 )) && exit $(( $1 - $2 ))")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'bash'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get("success"))
        self.assertFalse(result.get("error")[0]["hidden"])
        self.assert_correct_output("Error",
                                   result.get("error")[0]["message"])

    def test_infinite_loop(self):
        # Given
        user_answer = ("#!/bin/bash\nwhile [ 1 ] ;"
                       " do echo "" > /dev/null ; done")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'bash'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get("success"))
        self.assert_correct_output(self.timeout_msg,
                                   result.get("error")[0]["message"]
                                   )
        parent_proc = Process(os.getpid()).children()
        if parent_proc:
            children_procs = Process(parent_proc[0].pid)
            self.assertFalse(any(children_procs.children(recursive=True)))

    def test_file_based_assert(self):
        # Given
        self.file_paths = [(self.f_path, False)]
        self.tc_data = dedent("""
            #!/bin/bash
            cat $1
            """)
        self.tc_data_args = "test.txt"
        self.test_case_data = [{
            "test_case": self.tc_data,
            "test_case_args": self.tc_data_args,
            "test_case_type": "standardtestcase",
            "weight": 0.0,
            "hidden": True
        }]
        user_answer = ("#!/bin/bash\ncat $1")
        kwargs = {'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'bash'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get("success"))


class BashStdIOEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        self.in_dir = tempfile.mkdtemp()
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your"
                            " code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def test_correct_answer(self):
        # Given
        user_answer = dedent(""" #!/bin/bash
                             read A
                             read B
                             echo -n `expr $A + $B`
                             """
                             )
        test_case_data = [{
            'expected_output': '11',
            'expected_input': '5\n6',
            'test_case_type': 'stdiobasedtestcase',
            'weight': 0.0
            }]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'bash'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_array_input(self):
        # Given
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
                           'test_case_type': 'stdiobasedtestcase',
                           'weight': 0.0,
                           }]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'bash'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = dedent(""" #!/bin/bash
                             read A
                             read B
                             echo -n `expr $A - $B`
                             """
                             )
        test_case_data = [{
            'expected_output': '11',
            'expected_input': '5\n6',
            'test_case_type': 'stdiobasedtestcase',
            'weight': 0.0,
            'hidden': True
            }]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'bash'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        result_error = result.get('error')[0].get('error_msg')
        self.assert_correct_output("Incorrect", result_error)
        self.assertTrue(result.get('error')[0]['hidden'])
        self.assertFalse(result.get('success'))

    def test_stdout_only(self):
        # Given
        user_answer = dedent(""" #!/bin/bash
                             A=6
                             B=4
                             echo -n `expr $A + $B`
                             """
                             )
        test_case_data = [{'expected_output': '10',
                           'test_case_type': 'stdiobasedtestcase',
                           'weight': 0.0
                           }]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'bash'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))


class BashHookEvaluationTestCases(EvaluatorBaseTest):

    def setUp(self):
        self.f_path = os.path.join(tempfile.gettempdir(), "test.txt")
        with open(self.f_path, 'wb') as f:
            f.write('2'.encode('ascii'))
        self.in_dir = tempfile.mkdtemp()
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your"
                            " code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove(self.f_path)
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = dedent(""" #!/bin/bash
                             echo -n Hello, world!
                             """
                             )
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                import subprocess
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                proc = subprocess.Popen(
                                    user_answer, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
                                stdout,stderr = proc.communicate()
                                if stdout.decode("utf-8") == "Hello, world!":
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """)

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code, "weight": 1.0}]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'bash'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = dedent(""" #!/bin/bash
                             echo -n Goodbye, world!
                             """
                             )
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                import subprocess
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                proc = subprocess.Popen(
                                    user_answer, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
                                stdout,stderr = proc.communicate()
                                if stdout.decode("utf-8") == "Hello, world!":
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """)
        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code, "weight": 1.0,
                           "hidden": True}]

        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'bash'
                    }, 'test_case_data': test_case_data,
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
        user_answer = ("#!/bin/bash\n[[ $# -eq 2 ]]"
                       " && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))"
                       )
        assert_test_case = dedent("""
            #!/bin/bash
            [[ $# -eq 2 ]] && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))
            """)

        assert_test_case_args = "1 2\n2 1"

        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                if "echo $(( $1 + $2 ))" in user_answer:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """)

        test_case_data = [{"test_case_type": "standardtestcase",
                           "test_case": assert_test_case,
                           "test_case_args": assert_test_case_args,
                           'weight': 1.0
                           },
                          {"test_case_type": "hooktestcase",
                           "hook_code": hook_code, 'weight': 1.0,
                           'hidden': True},
                          ]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': True,
                    'language': 'bash'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get("weight"), 2.0)

    def test_multiple_hooks(self):
        # Given
        user_answer = dedent(""" #!/bin/bash
                             echo -n Hello, world!
                             """
                             )

        hook_code_1 = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                if "echo -n Hello, world!" in user_answer:
                                    success, err, mark_fraction = True, "", 0.5
                                return success, err, mark_fraction
                            """)
        hook_code_2 = dedent("""\
                    def check_answer(user_answer):
                        import subprocess
                        import sys
                        success = False
                        err = "Incorrect Answer"
                        mark_fraction = 0.0
                        proc = subprocess.Popen(user_answer, shell=True,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE
                                                )
                        stdout,stderr = proc.communicate()

                        if stdout.decode('utf-8') == "Hello, world!":
                            success, err, mark_fraction = True, "", 1.0
                        return success, err, mark_fraction
                    """)

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code_1, 'weight': 1.0},
                          {"test_case_type": "hooktestcase",
                           "hook_code": hook_code_2, 'weight': 1.0},
                          ]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': True,
                    'language': 'bash'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get("weight"), 1.5)

    def test_infinite_loop(self):
        # Given
        user_answer = ("#!/bin/bash\nwhile [ 1 ] ;"
                       " do echo "" > /dev/null ; done")

        hook_code = dedent("""\
                            def check_answer(user_answer):
                                import subprocess
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                proc = subprocess.Popen(
                                    user_answer, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
                                stdout,stderr = proc.communicate()
                                if stdout.decode("utf-8") == "Hello, world!":
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """)

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code, "weight": 1.0,
                           "hidden": False}]

        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'bash'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assert_correct_output(self.timeout_msg,
                                   result.get("error")[0]["message"]
                                   )
        parent_proc = Process(os.getpid()).children()
        if parent_proc:
            children_procs = Process(parent_proc[0].pid)
            self.assertFalse(any(children_procs.children(recursive=True)))


if __name__ == '__main__':
    unittest.main()
