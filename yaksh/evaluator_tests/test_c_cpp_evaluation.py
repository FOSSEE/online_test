from __future__ import absolute_import
import unittest
import os
import shutil
import tempfile
from textwrap import dedent
from psutil import Process

# Local import
from yaksh.grader import Grader
from yaksh.evaluator_tests.test_python_evaluation import EvaluatorBaseTest
from yaksh.settings import SERVER_TIMEOUT


class CAssertionEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        self.f_path = os.path.join(tempfile.gettempdir(), "test.txt")
        with open(self.f_path, 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.tc_data = dedent("""
            #include <stdio.h>
            #include <stdlib.h>

            extern int add(int, int);

            template <class T>

            void check(T expect, T result)
            {
                if (expect == result)
                {
                printf("Correct: Expected %d got %d ",expect,result);
                }
                else
                {
                printf("Incorrect: Expected %d got %d ",expect,result);
                exit (1);
               }
            }

            int main(void)
            {
                int result;
                result = add(0,0);
                    printf("Input submitted to the function: 0, 0");
                check(0, result);
                result = add(2,3);
                    printf("Input submitted to the function: 2 3");
                check(5,result);
                printf("All Correct");
                return 0;
            }
            """)
        self.test_case_data = [{"test_case": self.tc_data,
                                "test_case_type": "standardtestcase",
                                "weight": 0.0, "hidden": False
                                }]
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
        user_answer = "int add(int a, int b)\n{return a+b;}"
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = "int add(int a, int b)\n{return a-b;}"
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')
        # Then
        self.assertFalse(result.get('success'))
        for error in errors:
            self.assertEqual(error['exception'], 'AssertionError')

    def test_compilation_error(self):
        # Given
        user_answer = "int add(int a, int b)\n{return a+b}"
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')

        # Then
        self.assertFalse(result.get("success"))
        for error in errors:
            self.assertEqual(error['exception'], 'CompilationError')

    def test_infinite_loop(self):
        # Given
        user_answer = "int add(int a, int b)\n{while(1>0){}}"
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
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
            #include <stdio.h>
            #include <stdlib.h>

            extern int ans();

            template <class T>
            void check(T expect,T result)
            {
                if (expect == result)
                {
                printf("Correct: Expected %d got %d ",expect,result);
                }
                else
                {
                printf("Incorrect: Expected %d got %d ",expect,result);
                exit (0);
               }
            }

            int main(void)
            {
                int result;
                result = ans();
                check(50, result);
            }
            """)
        test_case_data = [{"test_case": self.tc_data,
                                "test_case_type": "standardtestcase",
                                "weight": 0.0,
                                }]
        user_answer = dedent("""
            #include<stdio.h>
            char ans()
            {
            FILE *fp;
            char buff[255];
            fp = fopen("test.txt", "r");
            fscanf(fp, "%s", buff);
            fclose(fp);
            return buff[0];
            }
            """)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_testcase(self):
        # Given
        self.tc_data = dedent("""
            #include <stdio.h>
            #include <stdlib.h>

            extern int add(int, int);

            template <class T>

            void check(T expect, T result)
            {
                if (expect == result)
                {
                printf("Correct: Expected %d got %d ",expect,result);
                }
                else
                {
                printf("Incorrect: Expected %d got %d ",expect,result);
                exit (1);
               }
            }

            int main(void)
            {
                int result;
                result = add(0,0);
                printf("Input submitted to the function: 0, 0");
                check(0, result);
                result = add(2,3);
                printf("Input submitted to the function: 2 3");
                check(5,result)
                printf("All Correct");
                return 0;
            }
            """)
        user_answer = dedent("""\
                        int add(int a, int b)
                        {
                        return a+b;
                        }""")
        test_case_data = [{"test_case": self.tc_data,
                                "test_case_type": "standardtestcase",
                                "weight": 0.0,
                                }]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get("error")

        # Then
        self.assertFalse(result.get('success'))
        for error in errors:
            self.assertEqual(error['exception'], 'TestCaseError')


class CppStdIOEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        self.test_case_data = [{'expected_output': '11',
                                'expected_input': '5\n6',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase',
                                'hidden': True
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
        #include<stdio.h>
        int main(void){
        int a,b;
        scanf("%d%d",&a,&b);
        printf("%d",a+b);
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_array_input(self):
        # Given
        test_case_data = [{'expected_output': '561',
                                'expected_input': '5\n6\n1',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase',
                                }]
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a[3],i;
        for(i=0;i<3;i++){
        scanf("%d",&a[i]);}
        for(i=0;i<3;i++){
        printf("%d",a[i]);}
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_string_input(self):
        # Given
        test_case_data = [{'expected_output': 'abc',
                                'expected_input': 'abc',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase',
                                }]
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        char a[4];
        scanf("%s",a);
        printf("%s",a);
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a=10;
        printf("%d",a);
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        lines_of_error = len(result.get('error')[0].get('error_line_numbers'))
        result_error = result.get('error')[0].get('error_msg')
        self.assertTrue(result.get('error')[0].get('hidden'))
        self.assertFalse(result.get('success'))
        self.assert_correct_output("Incorrect", result_error)
        self.assertTrue(lines_of_error > 0)

    def test_error(self):
        # Given
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a=10;
        printf("%d",a)
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')

        # Then
        self.assertFalse(result.get("success"))
        for error in errors:
            self.assertEqual(error['exception'], 'CompilationError')

    def test_infinite_loop(self):
        # Given
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        while(0==0){
        printf("abc");}
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
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

    def test_only_stdout(self):
        # Given
        test_case_data = [{'expected_output': '11',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase',
                                }]
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a=5,b=6;
        printf("%d",a+b);
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_cpp_correct_answer(self):
        # Given
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a,b;
        cin>>a>>b;
        cout<<a+b;
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('hidden'))
        self.assertTrue(result.get('success'))

    def test_cpp_array_input(self):
        # Given
        test_case_data = [{'expected_output': '561',
                                'expected_input': '5\n6\n1',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase',
                                }]
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a[3],i;
        for(i=0;i<3;i++){
        cin>>a[i];}
        for(i=0;i<3;i++){
        cout<<a[i];}
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_cpp_string_input(self):
        # Given
        test_case_data = [{'expected_output': 'abc',
                                'expected_input': 'abc',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase',
                                }]
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        char a[4];
        cin>>a;
        cout<<a;
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_cpp_incorrect_answer(self):
        # Given
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a=10;
        cout<<a;
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        lines_of_error = len(result.get('error')[0].get('error_line_numbers'))
        result_error = result.get('error')[0].get('error_msg')
        self.assertTrue(result.get('error')[0].get('hidden'))
        self.assertFalse(result.get('success'))
        self.assert_correct_output("Incorrect", result_error)
        self.assertTrue(lines_of_error > 0)

    def test_cpp_error(self):
        # Given
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a=10;
        cout<<a
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')

        # Then
        self.assertFalse(result.get("success"))
        for error in errors:
            self.assertEqual(error['exception'], 'CompilationError')

    def test_cpp_infinite_loop(self):
        # Given
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        while(0==0){
        cout<<"abc";}
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
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

    def test_cpp_only_stdout(self):
        # Given
        test_case_data = [{'expected_output': '11',
                               'expected_input': '',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase',
                                }]
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a=5,b=6;
        cout<<a+b;
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))


class CppHookEvaluationTestCases(EvaluatorBaseTest):

    def setUp(self):
        self.f_path = os.path.join(tempfile.gettempdir(), "test.txt")
        with open(self.f_path, 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
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
        user_answer = dedent("""\
                             #include<stdio.h>
                             main()
                             {
                                printf("Hello, world!");
                              }
                              """)
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                with open("Test.c", "w+") as f:
                                    f.write(user_answer)
                                import subprocess
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                def _run_command(cmd):
                                    proc = subprocess.Popen("{}".format(cmd),
                                                            shell=True,
                                                            stdout=subprocess.PIPE,
                                                            stderr=subprocess.PIPE
                                                            )
                                    stdout,stderr = proc.communicate()
                                    return stdout,stderr
                                cmds = ["gcc Test.c", "./a.out"]
                                for cmd in cmds:
                                    stdout, stderr = _run_command(cmd)
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
                    'language': 'cpp'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = dedent("""\
                             #include<stdio.h>
                             main()
                             {
                                printf("Goodbye, world!");
                              }
                              """)
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                with open("Test.c", "w+") as f:
                                    f.write(user_answer)
                                import subprocess
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                def _run_command(cmd):
                                    proc = subprocess.Popen(
                                        "{}".format(cmd), shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE
                                        )
                                    stdout,stderr = proc.communicate()
                                    return stdout,stderr
                                cmds = ["gcc Test.c", "./a.out"]
                                for cmd in cmds:
                                    stdout, stderr = _run_command(cmd)
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
                    'language': 'cpp'
                    }, 'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('error')[0]['hidden'])
        self.assertFalse(result.get('success'))
        self.assert_correct_output('Incorrect Answer',
                                   result.get('error')[0]['message'])

    def test_assert_with_hook(self):
        # Given
        user_answer = "int add(int a, int b)\n{return a+b;}"

        assert_test_case = dedent("""\
                          #include <stdio.h>
                          #include <stdlib.h>

                          extern int add(int, int);

                          template <class T>

                          void check(T expect, T result)
                          {
                              if (expect == result)
                              {
                              printf("Correct: Expected %d got %d ",
                                    expect,result);
                              }
                              else
                              {
                              printf("Incorrect: Expected %d got %d ",
                                    expect,result);
                              exit (1);
                             }
                          }

                          int main(void)
                          {
                              int result;
                              result = add(0,0);
                                  printf("Input submitted 0, 0");
                              check(0, result);
                              result = add(2,3);
                                  printf("Input submitted 2 3");
                              check(5,result);
                              printf("All Correct");
                              return 0;
                          }
                          """)

        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                if "return a+b;" in user_answer:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """)

        test_case_data = [{"test_case_type": "standardtestcase",
                           "test_case": assert_test_case,
                           'weight': 1.0
                           },
                          {"test_case_type": "hooktestcase",
                           "hook_code": hook_code, 'weight': 1.0},
                          ]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': True,
                    'language': 'cpp'
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
        user_answer = dedent("""\
                             #include<stdio.h>
                             main()
                             {
                                printf("Hello, world!");
                              }
                              """)

        hook_code_1 = dedent("""\
                            def check_answer(user_answer):
                                with open("Test.c", "w+") as f:
                                    f.write(user_answer)
                                import subprocess
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                def _run_command(cmd):
                                    proc = subprocess.Popen(
                                        "{}".format(cmd), shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE
                                    )
                                    stdout,stderr = proc.communicate()
                                    return stdout,stderr
                                cmds = ["gcc Test.c", "./a.out"]
                                for cmd in cmds:
                                    stdout, stderr = _run_command(cmd)
                                if stdout.decode("utf-8") == "Hello, world!":
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """)

        hook_code_2 = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                if 'printf("Hello, world!");' in user_answer:
                                    success, err, mark_fraction = True, "", 0.5
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
                    'language': 'cpp'
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
        user_answer = dedent("""\
                             #include<stdio.h>
                             int main(void){
                             while(0==0){
                             printf("abc");}
                             }""")

        hook_code = dedent("""\
                            def check_answer(user_answer):
                                with open("Test.c", "w+") as f:
                                    f.write(user_answer)
                                import subprocess
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                def _run_command(cmd):
                                    proc = subprocess.Popen(
                                        "{}".format(cmd), shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE
                                    )
                                    stdout,stderr = proc.communicate()
                                    return stdout,stderr
                                cmds = ["gcc Test.c", "./a.out"]
                                for cmd in cmds:
                                    stdout, stderr = _run_command(cmd)
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
                    'language': 'cpp'
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
