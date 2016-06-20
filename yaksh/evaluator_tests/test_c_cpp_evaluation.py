import unittest
import os
from yaksh.cpp_code_evaluator import CppCodeEvaluator
from yaksh.settings import SERVER_TIMEOUT
from textwrap import dedent

class CEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.test_case_data = [{"test_case": "c_cpp_files/main.cpp"}]
        self.in_dir = os.getcwd()
        self.timeout_msg = ("Code took more than {0} seconds to run. "
            "You probably have an infinite loop in your"
            " code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def test_correct_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b;}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
            'test_case_data': self.test_case_data,
            'file_paths': self.file_paths
        }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertEquals(result.get('error'), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "int add(int a, int b)\n{return a-b;}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer,
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect:", result.get('error'))
        self.assertTrue(result.get('error').splitlines > 1)

    def test_compilation_error(self):
        user_answer = "int add(int a, int b)\n{return a+b}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "int add(int a, int b)\n{while(1>0){}}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)

    def test_file_based_assert(self):
        self.file_paths = [(os.getcwd()+"/yaksh/test.txt", False)]
        self.test_case_data = [{"test_case": "c_cpp_files/file_data.c"}]
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
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data,
                  'file_paths': self.file_paths
                  }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertEquals(result.get('error'), "Correct answer")


if __name__ == '__main__':
    unittest.main()
