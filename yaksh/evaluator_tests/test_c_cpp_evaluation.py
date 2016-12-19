from __future__ import absolute_import
import unittest
import os
import shutil
import tempfile
from textwrap import dedent

# Local import
from yaksh.code_evaluator import CodeEvaluator
from yaksh.cpp_code_evaluator import CppCodeEvaluator
from yaksh.cpp_stdio_evaluator import CppStdioEvaluator
from yaksh.settings import SERVER_TIMEOUT



class CAssertionEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        with open('/tmp/test.txt', 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.test_case_data = [{"test_case": "c_cpp_files/main.cpp",
                                "test_case_type": "standardtestcase",
                                "weight": 0.0
                                }]
        self.in_dir = tmp_in_dir_path
        self.timeout_msg = ("Code took more than {0} seconds to run. "
            "You probably have an infinite loop in your"
            " code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove('/tmp/test.txt')
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b;}"
        # kwargs = {'user_answer': user_answer, 
        #     'partial_grading': False,
        #     'test_case_data': self.test_case_data,
        #     'file_paths': self.file_paths
        # }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('error'), "Correct answer\n")

    def test_incorrect_answer(self):
        user_answer = "int add(int a, int b)\n{return a-b;}"
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data,
        #             'file_paths': self.file_paths
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        lines_of_error = len(result.get('error').splitlines())
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect:", result.get('error'))
        self.assertTrue(lines_of_error > 1)

    def test_compilation_error(self):
        user_answer = "int add(int a, int b)\n{return a+b}"
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data,
        #             'file_paths': self.file_paths
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "int add(int a, int b)\n{while(1>0){}}"
        # get_class = CppCodeEvaluator(self.in_dir)
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data,
        #             'file_paths': self.file_paths
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), self.timeout_msg)

    def test_file_based_assert(self):
        self.file_paths = [('/tmp/test.txt', False)]
        self.test_case_data = [{"test_case": "c_cpp_files/file_data.c",
                                "test_case_type": "standardtestcase",
                                "weight": 0.0
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
        # get_class = CppCodeEvaluator(self.in_dir)
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data,
        #             'file_paths': self.file_paths
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('error'), "Correct answer\n")

class CppStdioEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.test_case_data = [{'expected_output': '11',
                                'expected_input': '5\n6',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase',
                                }]
        self.in_dir = tempfile.mkdtemp()
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def test_correct_answer(self):
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a,b;
        scanf("%d%d",&a,&b);
        printf("%d",a+b);
        }""")
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertEqual(result.get('error'), "Correct answer\n")
        self.assertTrue(result.get('success'))

    def test_array_input(self):
        self.test_case_data = [{'expected_output': '561',
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
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertEqual(result.get('error'), "Correct answer\n")
        self.assertTrue(result.get('success'))

    def test_string_input(self):
        self.test_case_data = [{'expected_output': 'abc',
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
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertEqual(result.get('error'), "Correct answer\n")
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a=10;
        printf("%d",a);
        }""")
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        lines_of_error = len(result.get('error').splitlines())
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect", result.get('error'))
        self.assertTrue(lines_of_error > 1)

    def test_error(self):
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a=10;
        printf("%d",a)
        }""")
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        while(0==0){
        printf("abc");}
        }""")
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), self.timeout_msg)

    def test_only_stdout(self):
        self.test_case_data = [{'expected_output': '11',
                               'expected_input': '',
                                'weight': 0.0,
                                'test_case_type': 'stdiobasedtestcase',
                                }]
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a=5,b=6;
        printf("%d",a+b);
        }""")
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertEqual(result.get('error'), "Correct answer\n")
        self.assertTrue(result.get('success'))

    def test_cpp_correct_answer(self):
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a,b;
        cin>>a>>b;
        cout<<a+b;
        }""")
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertEqual(result.get('error'), "Correct answer\n")
        self.assertTrue(result.get('success'))

    def test_cpp_array_input(self):
        self.test_case_data = [{'expected_output': '561',
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
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertEqual(result.get('error'), "Correct answer\n")
        self.assertTrue(result.get('success'))

    def test_cpp_string_input(self):
        self.test_case_data = [{'expected_output': 'abc',
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
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertEqual(result.get('error'), "Correct answer\n")
        self.assertTrue(result.get('success'))

    def test_cpp_incorrect_answer(self):
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a=10;
        cout<<a;
        }""")
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        lines_of_error = len(result.get('error').splitlines())
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect", result.get('error'))
        self.assertTrue(lines_of_error > 1)

    def test_cpp_error(self):
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a=10;
        cout<<a
        }""")
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_cpp_infinite_loop(self):
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        while(0==0){
        cout<<"abc";}
        }""")
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), self.timeout_msg)

    def test_cpp_only_stdout(self):
        self.test_case_data = [{'expected_output': '11',
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
        # get_class = CppStdioEvaluator()
        # kwargs = {'user_answer': user_answer,
        #             'partial_grading': False,
        #             'test_case_data': self.test_case_data
        #         }
        # result = get_class.evaluate(**kwargs)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'cpp'
                    },
                    'test_case_data': self.test_case_data,
                  }

        evaluator = CodeEvaluator(self.in_dir)
        result = evaluator.evaluate(kwargs)

        self.assertEqual(result.get('error'), "Correct answer\n")
        self.assertTrue(result.get('success'))

if __name__ == '__main__':
    unittest.main()
