from __future__ import absolute_import
import unittest
import os
import shutil
import tempfile
from textwrap import dedent
from psutil import Process

from yaksh.grader import Grader
from yaksh.ruby_assertion_evaluator import rubyCodeEvaluator
from yaksh.ruby_stdio_evaluator import RubyStdIOEvaluator
from yaksh.evaluator_tests.test_python_evaluation import EvaluatorBaseTest
from yaksh.settings import SERVER_TIMEOUT

class RubyAssertionEvalutionTestCases(EvaluatorBaseTest):
    def setUp(self):
        self.f_path = os.path.join(tempfile.gettempdir(),"test.txt")
        with open(self.f_path, 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.tc_data=dedent("""
        class AssertionError < StandardError
        end

        def assert(message=nil, &block)
          unless(block.call)
            raise AssertionError, (message || "Assertion failed")
          end
        end
""")
        self.test_case_data = [{"test_case": '{0}\n{1}'.format(self.tc_data,'assert{add(1,2)==3}'),
                                "test_case_type": "standardtestcase",
                                "weight": 0.0
                                },
                                {"test_case": '{0}\n{1}'.format(self.tc_data,'assert{add(-1,2)==1}'),
                                "test_case_type": "standardtestcase",
                                "weight": 0.0
                                },
                                {"test_case": '{0}\n{1}'.format(self.tc_data,'assert{add(-2,1)==-1}'),
                                "test_case_type": "standardtestcase",
                                "weight": 0.0
                                },]
        self.in_dir = tmp_in_dir_path
        self.timeout_msg = ("Code took more than {0} seconds to run. "
            "You probably have an infinite loop in your"
            " code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove(self.f_path)
        shutil.rmtree(self.in_dir)


    def test_correct_answer(self):
        # Given
        user_answer = "\ndef add(a,b)\n\treturn a+b\nend\n"
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'ruby'
                    },
                    'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = dedent("""
        def add(a, b)
          return a-b
        end
        """)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'ruby'
                    },
                    'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
         
        lines_of_error = len(result.get('error')[0].splitlines())
        self.assertFalse(result.get('success'))
        self.assert_correct_output("Error", result.get('error'))
        self.assertTrue(lines_of_error > 1)

    def test_partial_incorrect_answer(self):
        # Given
        user_answer = "\ndef add(a,b):\n\treturn a.abs + b.abs\nend\n"
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': True,
                  'language': 'ruby'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        self.assertFalse(result.get('success'))
    
    def test_infinite_loop(self):
        # Given
        user_answer = "\ndef add(a, b)\n\twhile true\n\tend\nend\n"
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'ruby'},
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


    def test_syntax_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b):
          return a + b
        end
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
                  'language': 'ruby'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        lines_of_error = len(result.get('error')[0].splitlines())
        self.assertFalse(result.get('success'))
        self.assert_correct_output("Error", result.get('error'))
        self.assertTrue(lines_of_error > 1)

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
                  'language': 'ruby'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        self.assertFalse(result.get('success'))
    
    def test_recursion_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b)
          return add(3, 3)
        end
        """)
        recursion_error_msg = "maximum recursion depth exceeded"
        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'ruby'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        # Then
        err="maximum recursion depth exceeded"
        self.assertFalse(result.get("success"))
        self.assert_correct_output(recursion_error_msg, err)


    def test_type_error(self):
        # Given
        user_answer = dedent("""
        def add(a)
         return a + b
        end        
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
                  'language': 'ruby'},
                  'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        lines_of_error = len(result.get('error')[0].splitlines())
        self.assertFalse(result.get('success'))
        self.assert_correct_output("Error", result.get('error'))
        self.assertTrue(lines_of_error > 1)
        

class RubyStdIOEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        self.test_case_data = [{'expected_output': '11',
                                'expected_input': '5\n6',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase'
                                }]
        self.in_dir = tempfile.mkdtemp()
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = dedent("""
        val1 = gets
        val2 = gets
        print (val1.to_i + val2.to_i)
        """)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'ruby'
                    },
                    'test_case_data': self.test_case_data
                 }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = dedent("""
            val1 = gets
            val2 = gets
            print (val1.to_i * val2.to_i)
        """)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'ruby'
                    },
                    'test_case_data': self.test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        lines_of_error = len(result.get('error')[0].get('error_line_numbers'))
        result_error = result.get('error')[0].get('error_msg')
        print(lines_of_error,result_error)
        self.assertFalse(result.get('success'))
        self.assert_correct_output("Incorrect", result_error)
        self.assertTrue(lines_of_error > 0)

    def test_infinite_loop(self):
        # Given
        user_answer = dedent("""
         m=1
         loop do
          puts "232"
          m+=1
          break if m==0
         end
        """)
        timeout_msg = ("Code took more than {0} seconds to run. "
                       "You probably have an infinite loop in"
                       " your code.").format(SERVER_TIMEOUT)

        kwargs = {'metadata': {
                  'user_answer': user_answer,
                  'file_paths': self.file_paths,
                  'partial_grading': False,
                  'language': 'ruby'},
                  'test_case_data': self.test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assert_correct_output(timeout_msg,
                                   result.get("error")[0]['message']
                                   )
        self.assertFalse(result.get('success'))
        parent_proc = Process(os.getpid()).children()
        if parent_proc:
            children_procs = Process(parent_proc[0].pid)
            self.assertFalse(any(children_procs.children(recursive=True)))

    def test_error(self):
        user_answer = dedent("""
         puts "12":
        """)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'ruby'
                    },
                    'test_case_data': self.test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get("success"))
        #self.assert_correct_output("Compilation Error", result.get("error")[0]['error_msg'])

    def test_only_stdout(self):
        # Given
        self.test_case_data = [{'expected_output': '11',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase'
                                }]
        user_answer = dedent("""
        print("11")
        """)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'ruby'
                    },
                    'test_case_data': self.test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))


    def test_array_input(self):
        # Given
        self.test_case_data = [{'expected_output': '561',
                                'expected_input': '5\n6\n1',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase',
                                }]
        user_answer = dedent("""
        a=Array.new(3)
        for i in 0..2
         b=gets
         a[i]=b.to_i
        end
        for i in 0..2
         print(a[i])
        end
        """)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'ruby'
                    },
                    'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))


    def test_rb_string_input(self):
        # Given
        self.test_case_data = [{'expected_output': 'abc',
                                'expected_input': 'abc',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase'
                                }]
        user_answer = dedent("""
        a=gets;
        for i in 0..2;
        print(a[i]);
        end
        """)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'ruby'
                    },
                    'test_case_data': self.test_case_data
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))
