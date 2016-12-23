from __future__ import unicode_literals
import unittest
import os
import shutil
import tempfile

from yaksh import grader as gd
from yaksh.grader import Grader
from yaksh.scilab_code_evaluator import ScilabCodeEvaluator
from yaksh.evaluator_tests.test_python_evaluation import EvaluatorBaseTest


class ScilabEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        tmp_in_dir_path = tempfile.mkdtemp()
        self.test_case_data = [{"test_case": "scilab_files/test_add.sce",
                                "test_case_type": "standardtestcase",
                                "weight": 0.0
                                }]
        self.in_dir = tmp_in_dir_path
        self.file_paths = None
        gd.SERVER_TIMEOUT = 9
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop" 
                            " in your code.").format(gd.SERVER_TIMEOUT)

    def tearDown(self):
        gd.SERVER_TIMEOUT = 4
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        user_answer = ("funcprot(0)\nfunction[c]=add(a,b)"
                        "\n\tc=a+b;\nendfunction")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'scilab'
                    },
                    'test_case_data': self.test_case_data,
                  }

        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        self.assertTrue(result.get('success'))

    def test_error(self):
        user_answer = ("funcprot(0)\nfunction[c]=add(a,b)"
                        "\n\tc=a+b;\ndis(\tendfunction")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'scilab'
                    },
                    'test_case_data': self.test_case_data,
                  }

        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        self.assertFalse(result.get("success"))
        self.assert_correct_output('error', result.get("error"))


    def test_incorrect_answer(self):
        user_answer = ("funcprot(0)\nfunction[c]=add(a,b)"
                        "\n\tc=a-b;\nendfunction")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'scilab'
                    },
                    'test_case_data': self.test_case_data,
                  }

        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        lines_of_error = len(result.get('error')[0].splitlines())
        self.assertFalse(result.get('success'))
        self.assert_correct_output("Message", result.get('error'))
        self.assertTrue(lines_of_error > 1)

    def test_infinite_loop(self):
        user_answer = ("funcprot(0)\nfunction[c]=add(a,b)"
                        "\n\tc=a;\nwhile(1==1)\nend\nendfunction")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'scilab'
                    },
                    'test_case_data': self.test_case_data,
                  }

        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        self.assertFalse(result.get("success"))
        self.assert_correct_output(self.timeout_msg, result.get("error"))

if __name__ == '__main__':
    unittest.main()
