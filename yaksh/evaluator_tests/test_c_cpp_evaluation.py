import unittest
import os
from yaksh.cpp_code_evaluator import CppCodeEvaluator
from yaksh.cpp_stdio_evaluator import CppStdioEvaluator
from yaksh.settings import SERVER_TIMEOUT
from textwrap import dedent


class CAssertionEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.test_case_data = [{"test_case": "c_cpp_files/main.cpp"}]
        self.in_dir = "/tmp"
        self.timeout_msg = ("Code took more than {0} seconds to run. "
            "You probably have an infinite loop in your"
            " code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b;}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
            'test_case_data': self.test_case_data
        }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertEquals(result.get('error'), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "int add(int a, int b)\n{return a-b;}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer,
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect:", result.get('error'))
        self.assertTrue(result.get('error').splitlines > 1)

    def test_compilation_error(self):
        user_answer = "int add(int a, int b)\n{return a+b}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "int add(int a, int b)\n{while(1>0){}}"
        get_class = CppCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)


class CppStdioEvaluationTestCases(unittest.TestCase):

    def setUp(self):
        self.test_case_data = [{'expected_output': '11', 'expected_input': '5\n6'}]
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a,b;
        scanf("%d%d",&a,&b);
        printf("%d",a+b);
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

    def test_array_input(self):
        self.test_case_data = [{'expected_output': '561',
                                'expected_input': '5\n6\n1'}]
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a[3],i;
        for(i=0;i<3;i++){
        scanf("%d",&a[i]);}
        for(i=0;i<3;i++){
        printf("%d",a[i]);}
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

    def test_string_input(self):
        self.test_case_data = [{'expected_output': 'abc',
                                'expected_input': 'abc'}]
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        char a[4];
        scanf("%s",a);
        printf("%s",a);
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a=10;
        printf("%d",a);
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect", result.get('error'))
        self.assertTrue(result.get('error').splitlines > 1)

    def test_error(self):
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a=10;
        printf("%d",a)
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        while(0==0){
        printf("abc");}
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)

    def test_only_stdout(self):
        self.test_case_data = [{'expected_output': '11',
                               'expected_input': ''}]
        user_answer = dedent("""
        #include<stdio.h>
        int main(void){
        int a=5,b=6;
        printf("%d",a+b);
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
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
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

    def test_cpp_array_input(self):
        self.test_case_data = [{'expected_output': '561',
                                'expected_input': '5\n6\n1'}]
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
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

    def test_cpp_string_input(self):
        self.test_case_data = [{'expected_output': 'abc',
                                'expected_input': 'abc'}]
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        char a[4];
        cin>>a;
        cout<<a;
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

    def test_cpp_incorrect_answer(self):
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a=10;
        cout<<a;
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect", result.get('error'))
        self.assertTrue(result.get('error').splitlines > 1)

    def test_cpp_error(self):
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a=10;
        cout<<a
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
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
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)

    def test_cpp_only_stdout(self):
        self.test_case_data = [{'expected_output': '11',
                               'expected_input': ''}]
        user_answer = dedent("""
        #include<iostream>
        using namespace std;
        int main(void){
        int a=5,b=6;
        cout<<a+b;
        }""")
        get_class = CppStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

if __name__ == '__main__':
    unittest.main()
