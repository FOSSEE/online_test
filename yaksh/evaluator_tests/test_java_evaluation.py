import unittest
import os
from yaksh import code_evaluator as evaluator
from yaksh.java_code_evaluator import JavaCodeEvaluator
from yaksh.java_stdio_evaluator import JavaStdioEvaluator
from yaksh.settings import SERVER_TIMEOUT
from textwrap import dedent


class JavaAssertionEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.test_case_data = [
            {"test_case": "java_files/main_square.java"}
        ]
        self.in_dir = "/tmp"
        evaluator.SERVER_TIMEOUT = 9
        self.timeout_msg = ("Code took more than {0} seconds to run. "
            "You probably have an infinite loop in"
            " your code.").format(evaluator.SERVER_TIMEOUT)

    def tearDown(self):
        evaluator.SERVER_TIMEOUT = 2

    def test_correct_answer(self):
        user_answer = "class Test {\n\tint square_num(int a) {\n\treturn a*a;\n\t}\n}"
        get_class = JavaCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct answer")
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        user_answer = "class Test {\n\tint square_num(int a) {\n\treturn a;\n\t}\n}"
        get_class = JavaCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect:", result.get('error'))
        self.assertTrue(result.get('error').splitlines > 1)

    def test_error(self):
        user_answer = "class Test {\n\tint square_num(int a) {\n\treturn a*a"
        get_class = JavaCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs) 
        self.assertFalse(result.get("success"))
        self.assertTrue("Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "class Test {\n\tint square_num(int a) {\n\t\twhile(0==0){\n\t\t}\n\t}\n}"
        get_class = JavaCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs) 
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)


class JavaStdioEvaluationTestCases(unittest.TestCase):

    def setUp(self):
        self.test_case_data = [{'expected_output': '11',
                               'expected_input': '5\n6'}]
        evaluator.SERVER_TIMEOUT = 4
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(evaluator.SERVER_TIMEOUT)

    def teardown(self):
        evaluator.SERVER_TIMEOUT = 4

    def test_correct_answer(self):
        user_answer = dedent("""
        import java.util.Scanner;
        class Test
        {public static void main(String[] args){
         Scanner s = new Scanner(System.in);
         int a = s.nextInt();
         int b = s.nextInt();
         System.out.print(a+b);
        }}""")
        get_class = JavaStdioEvaluator()
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
        import java.util.Scanner;
        class Test
        {public static void main(String[] args){
         Scanner s = new Scanner(System.in);
         int a[] = new int[3];
         for (int i=0;i<3;i++){
         a[i] = s.nextInt();
         System.out.print(a[i]);}
        }}""")
        get_class = JavaStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):

        user_answer = dedent("""
        import java.util.Scanner;
        class Test
        {public static void main(String[] args){
         Scanner s = new Scanner(System.in);
         int a = s.nextInt();
         int b = s.nextInt();
         System.out.print(a);
        }}""")
        get_class = JavaStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertIn("Incorrect", result.get('error'))
        self.assertTrue(result.get('error').splitlines > 1)

    def test_error(self):

        user_answer = dedent("""
        class Test
        {
         System.out.print("a");
        }""")
        get_class = JavaStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):

        user_answer = dedent("""
        class Test
        {public static void main(String[] args){
         while(0==0)
         {
         System.out.print("a");}
        }}""")
        get_class = JavaStdioEvaluator()
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
        class Test
        {public static void main(String[] args){
         int a = 5;
         int b = 6;
         System.out.print(a+b);
        }}""")
        get_class = JavaStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

    def test_string_input(self):
        self.test_case_data = [{'expected_output': 'HelloWorld',
                               'expected_input': 'Hello\nWorld'}]
        user_answer = dedent("""
        import java.util.Scanner;
        class Test
        {public static void main(String[] args){
         Scanner s = new Scanner(System.in);
         String a = s.nextLine();
         String b = s.nextLine();
         System.out.print(a+b);
        }}""")
        get_class = JavaStdioEvaluator()
        kwargs = {'user_answer': user_answer,
                  'test_case_data': self.test_case_data
                  }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct Answer")
        self.assertTrue(result.get('success'))

if __name__ == '__main__':
    unittest.main()
