from __future__ import unicode_literals
import unittest
from textwrap import dedent
import os
import tempfile
import shutil
from psutil import Process

from yaksh.grader import Grader
from yaksh.settings import SERVER_TIMEOUT
from yaksh.evaluator_tests.test_python_evaluation import EvaluatorBaseTest


class RAssertionEvaluationTestCase(EvaluatorBaseTest):
    def setUp(self):
        self.tmp_file = os.path.join(tempfile.gettempdir(), 'test.txt')
        with open(self.tmp_file, 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path
        self.test_case = dedent(
            '''
            source("function.r")
            check_empty = function(obj){
                stopifnot(is.null(obj) == FALSE)
            }
            check = function(input, output){
            stopifnot(input == output)
            }
            is_correct = function(){
            if (count == 3){
                quit("no", 31)
            }
            }
            check_empty(odd_or_even(3))
            check(odd_or_even(6), "EVEN")
            check(odd_or_even(1), "ODD")
            check(odd_or_even(10), "EVEN")
            check(odd_or_even(777), "ODD")
            check(odd_or_even(778), "EVEN")
            count = 3
            is_correct()
            '''
        )
        self.test_case_data = [{"test_case": self.test_case,
                                "test_case_type": "standardtestcase",
                                "weight": 0.0, "hidden": True
                                }]
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove(self.tmp_file)
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = dedent(
            '''
            odd_or_even <- function(n){
              if(n %% 2 == 0){
                return("EVEN")
              }
              return("ODD")
            }
            '''
        )
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'r'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = dedent(
            '''
            odd_or_even <- function(n){
              if(n %% 2 == 0){
                return("ODD")
              }
              return("EVEN")
            }
            '''
        )
        err = 'input == output is not TRUE\nExecution halted\n'
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'r'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')
        # Then
        self.assertTrue(result.get("error")[0]['hidden'])
        self.assertFalse(result.get('success'))
        self.assertEqual(errors[0]['message'], err)

    def test_error_code(self):
        # Given
        user_answer = dedent(
            '''
            odd_or_even <- function(n){
             a
            }
            '''
        )
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'r'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')

        # Then
        self.assertTrue(result.get("error")[0]['hidden'])
        self.assertFalse(result.get("success"))
        self.assertIn("object 'a' not found", errors[0]['message'])

    def test_empty_function(self):
        # Given
        user_answer = dedent(
            '''
            odd_or_even <- function(n){
            }
            '''
        )
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'r'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')

        # Then
        self.assertTrue(result.get("error")[0]['hidden'])
        self.assertFalse(result.get("success"))
        err = errors[0]['message']
        self.assertIn("is.null(obj) == FALSE is not TRUE", err)

    def test_infinite_loop(self):
        # Given
        user_answer = dedent(
            '''
            odd_or_even <- function(n){
              while(0 == 0){
                a <- 1
              }
            }
            '''
        )
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'r'},
                  'test_case_data': self.test_case_data,
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
