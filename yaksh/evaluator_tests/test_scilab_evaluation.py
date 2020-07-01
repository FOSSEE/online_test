from __future__ import unicode_literals
import unittest
import os
import shutil
import tempfile
from psutil import Process
from textwrap import dedent

# Local Import
from yaksh import grader as gd
from yaksh.grader import Grader
from yaksh.evaluator_tests.test_python_evaluation import EvaluatorBaseTest


class ScilabEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        tmp_in_dir_path = tempfile.mkdtemp()
        self.tc_data = dedent("""
            mode(-1)
            exec("function.sci",-1);
            i = 0
            p = add(3,5);
            correct = (p == 8);
            if correct then
             i=i+1
            end
            disp("Input submitted 3 and 5")
            disp("Expected output 8 got " + string(p))
            p = add(22,-20);
            correct = (p==2);
            if correct then
             i=i+1
            end
            disp("Input submitted 22 and -20")
            disp("Expected output 2 got " + string(p))
            p =add(91,0);
            correct = (p==91);
            if correct then
             i=i+1
            end
            disp("Input submitted 91 and 0")
            disp("Expected output 91 got " + string(p))
            if i==3 then
             exit(5);
            else
             exit(3);
            end
            """)
        self.test_case_data = [{"test_case": self.tc_data,
                                "test_case_type": "standardtestcase",
                                "weight": 0.0, 'hidden': True
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
                    }, 'test_case_data': self.test_case_data,
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
                    }, 'test_case_data': self.test_case_data,
                  }

        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        self.assertFalse(result.get("success"))
        self.assertTrue(result.get("error")[0]['hidden'])
        self.assert_correct_output('error', result.get("error")[0]['message'])

    def test_incorrect_answer(self):
        user_answer = ("funcprot(0)\nfunction[c]=add(a,b)"
                       "\n\tc=a-b;\nendfunction")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'scilab'
                    }, 'test_case_data': self.test_case_data,
                  }

        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        lines_of_error = len(result.get('error')[0]['message'].splitlines())
        self.assertFalse(result.get('success'))
        self.assertTrue(result.get("error")[0]['hidden'])
        self.assert_correct_output("Message",
                                   result.get('error')[0]["message"])
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
                    }, 'test_case_data': self.test_case_data,
                  }

        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        self.assertFalse(result.get("success"))
        self.assert_correct_output(self.timeout_msg,
                                   result.get("error")[0]["message"]
                                   )
        parent_proc = Process(os.getpid()).children()
        if parent_proc:
            children_procs = Process(parent_proc[0].pid)
            self.assertFalse(any(children_procs.children(recursive=True)))


if __name__ == '__main__':
    unittest.main()
