from __future__ import unicode_literals
import unittest
import os
import shutil
import tempfile
from textwrap import dedent
from psutil import Process


# Local Import
from yaksh import grader as gd
from yaksh.grader import Grader
from yaksh.evaluator_tests.test_python_evaluation import EvaluatorBaseTest


class JavaAssertionEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        self.f_path = os.path.join(tempfile.gettempdir(), "test.txt")
        with open(self.f_path, 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.tc_data = dedent("""
            class main
            {
                public static <E> void check(E expect, E result)
                {
                    if(result.equals(expect))
                    {
                        System.out.println("Correct:Output expected "+expect+
                                            "and got "+result);
                    }
                else
                {
                    System.out.println("Incorrect:Output expected "+expect+
                                        "but got "+result);
                    System.exit(1);
                }
                }
                public static void main(String arg[])
                {
                   Test t = new Test();
                   int result, input, output;
                   input = 0; output = 0;
                   result = t.square_num(input);
                   System.out.println("Input submitted to the function: "+
                                    input);
                   check(output, result);
                   input = 5; output = 25;
                   result = t.square_num(input);
                   System.out.println("Input submitted to the function: "+
                                    input);
                   check(output, result);
                   input = 6; output = 36;
                   result = t.square_num(input);
                   System.out.println("Input submitted to the function: "+
                                    input);
                   check(output, result);
                }
            }
            """)

        self.test_case_data = [
            {"test_case": self.tc_data,
             "test_case_type": "standardtestcase",
             "weight": 0.0, "hidden": False
             }
        ]
        self.in_dir = tmp_in_dir_path
        self.file_paths = None
        gd.SERVER_TIMEOUT = 9
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(gd.SERVER_TIMEOUT)

    def tearDown(self):
        gd.SERVER_TIMEOUT = 4
        os.remove(self.f_path)
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = ("class Test {\n\tint square_num(int a)"
                       " {\n\treturn a*a;\n\t}\n}")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = ("class Test {\n\tint square_num(int a) "
                       "{\n\treturn a;\n\t}\n}")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')

        # Then
        self.assertFalse(result.get('success'))
        for error in errors:
            self.assertEqual(error.get('exception'), 'AssertionError')
            self.assertFalse(error.get('hidden'))

    def test_error(self):
        # Given
        user_answer = "class Test {\n\tint square_num(int a) {\n\treturn a*a}"
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')
        # Then
        self.assertFalse(result.get("success"))
        for error in errors:
            self.assertEqual(error.get('exception'), 'CompilationError')
            self.assertFalse(result.get('hidden'))

    def test_infinite_loop(self):
        # Given
        user_answer = ("class Test {\n\tint square_num(int a)"
                       " {\n\t\twhile(0==0){\n\t\t}\n\t}\n}")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
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
            class main
            {
                public static <E> void check(E expect, E result)
                {
                    if(result.equals(expect))
                    {
                        System.out.println("Correct:Output expected "+expect+
                                            " and got "+result);
                    }
                else
                {
                    System.out.println("Incorrect:Output expected "+expect+
                                        " but got "+result);
                    System.exit(1);
                }
                }
                public static void main(String arg[])
                {
                   String result = "";
                   Test t = new Test();
                   try{
                   result = t.readFile();}
                   catch(Exception e){
                System.out.print(e);
                }
                   check("2", result);
                }
            }
            """)
        self.test_case_data = [
            {"test_case": self.tc_data,
             "test_case_type": "standardtestcase",
             "weight": 0.0
             }
        ]
        user_answer = dedent("""
            import java.io.BufferedReader;
            import java.io.FileReader;
            import java.io.IOException;
            class Test{
            String readFile() throws IOException {
            BufferedReader br = new BufferedReader(new FileReader("test.txt"));
            try {
                StringBuilder sb = new StringBuilder();
                String line = br.readLine();
                while (line != null) {
                    sb.append(line);
                    line = br.readLine();}
                return sb.toString();
            } finally {
                br.close();
            }}}
            """)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get("success"))

    def test_incorrect_testcase(self):
        # Given
        self.tc_data = dedent("""
            class main
            {
                public static <E> void check(E expect, E result)
                {
                    if(result.equals(expect))
                    {
                        System.out.println("Correct:Output expected "+expect+
                                            "and got "+result);
                    }
                else
                {
                    System.out.println("Incorrect:Output expected "+expect+
                                        "but got "+result);
                    System.exit(1);
                }
                }
                public static void main(String arg[])
                {
                   Test t = new Test();
                   int result, input, output;
                   input = 0; output = 0;
                   result = t.square_num(input);
                   System.out.println("Input submitted to the function: "+
                                    input);
                   check(output, result)
                }
            }
            """)
        user_answer = ("class Test {\n\tint square_num(int a) "
                       "{\n\treturn a;\n\t}\n}")
        self.test_case_data = [{"test_case": self.tc_data,
                                "test_case_type": "standardtestcase",
                                "weight": 0.0, "hidden": True
                                }]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')

        # Then
        self.assertFalse(result.get('success'))
        for error in errors:
            self.assertEqual(error.get('exception'), 'TestCaseError')


class JavaStdIOEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        self.f_path = os.path.join(tempfile.gettempdir(), "test.txt")
        with open(self.f_path, 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path
        self.test_case_data = [{'expected_output': '11',
                                'expected_input': '5\n6',
                                'test_case_type': 'stdiobasedtestcase',
                                'weight': 0.0
                                }]
        self.file_paths = None
        gd.SERVER_TIMEOUT = 9
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(gd.SERVER_TIMEOUT)

    def tearDown(self):
        gd.SERVER_TIMEOUT = 4
        os.remove(self.f_path)
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = dedent("""
        import java.util.Scanner;
        class Test
        {public static void main(String[] args){
         Scanner s = new Scanner(System.in);
         int a = s.nextInt();
         int b = s.nextInt();
         System.out.print(a+b);
        }}""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
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
                                'test_case_type': 'stdiobasedtestcase',
                                'weight': 0.0
                                }]
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
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = dedent("""
        import java.util.Scanner;
        class Test
        {public static void main(String[] args){
         Scanner s = new Scanner(System.in);
         int a = s.nextInt();
         int b = s.nextInt();
         System.out.print(a);
        }}""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        lines_of_error = len(result.get('error')[0].get('error_line_numbers'))
        result_error = result.get('error')[0].get('error_msg')
        self.assertFalse(result.get('error')[0].get('hidden'))
        self.assertFalse(result.get('success'))
        self.assert_correct_output("Incorrect", result_error)
        self.assertTrue(lines_of_error > 0)

    def test_error(self):
        # Given
        user_answer = dedent("""
        class Test
        {
         System.out.print("a");
        }""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        errors = result.get('error')

        # Then
        self.assertFalse(result.get("success"))
        for error in errors:
            self.assertEqual(error.get('exception'), 'CompilationError')
            self.assertFalse(error.get('hidden'))

    def test_infinite_loop(self):
        # Given
        user_answer = dedent("""
        class Test
        {public static void main(String[] args){
         while(0==0)
         {
         System.out.print("a");}
        }}""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
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
        self.test_case_data = [{'expected_output': '11',
                                'test_case_type': 'stdiobasedtestcase',
                                'weight': 0.0, 'hidden': False
                                }]
        user_answer = dedent("""
        class Test
        {public static void main(String[] args){
         int a = 5;
         int b = 6;
         System.out.print(a+b);
        }}""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_string_input(self):
        # Given
        self.test_case_data = [{'expected_output': 'HelloWorld',
                                'expected_input': 'Hello\nWorld',
                                'test_case_type': 'stdiobasedtestcase',
                                'weight': 0.0
                                }]
        user_answer = dedent("""
        import java.util.Scanner;
        class Test
        {public static void main(String[] args){
         Scanner s = new Scanner(System.in);
         String a = s.nextLine();
         String b = s.nextLine();
         System.out.print(a+b);
        }}""")
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_file_based_stdout(self):
        # Given
        self.file_paths = [(self.f_path, False)]
        self.test_case_data = [{'expected_output': '2',
                                'expected_input': '',
                                'test_case_type': 'stdiobasedtestcase',
                                'weight': 0.0
                                }]
        user_answer = dedent("""
            import java.io.BufferedReader;
            import java.io.FileReader;
            import java.io.IOException;
            class Test{
            public static void main(String[] args) throws IOException {
            BufferedReader br = new BufferedReader(new FileReader("test.txt"));
            try {
                StringBuilder sb = new StringBuilder();
                String line = br.readLine();
                while (line != null) {
                    sb.append(line);
                    line = br.readLine();}
                System.out.print(sb.toString());
            } finally {
                br.close();
            }}}
            """)
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
                    }, 'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get("success"))


class JavaHookEvaluationTestCases(EvaluatorBaseTest):

    def setUp(self):
        self.f_path = os.path.join(tempfile.gettempdir(), "test.txt")
        with open(self.f_path, 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path
        self.file_paths = None
        gd.SERVER_TIMEOUT = 9
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(gd.SERVER_TIMEOUT)

    def tearDown(self):
        gd.SERVER_TIMEOUT = 4
        os.remove(self.f_path)
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = dedent("""\
                             class Test
                             {public static void main(String[] args){
                             System.out.print("Hello, world!");
                             }}
                             """)
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                with open("Test.java", "w+") as f:
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
                                cmds = ["javac Test.java", "java Test"]
                                for cmd in cmds:
                                    stdout, stderr = _run_command(cmd)
                                if stdout.decode("utf-8") == "Hello, world!":
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """)

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code, "weight": 1.0
                           }]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
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
                             class Test
                             {public static void main(String[] args){
                             System.out.print("Goodbye, world!");
                             }}
                             """)
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                with open("Test.java", "w+") as f:
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
                                cmds = ["javac Test.java", "java Test"]
                                for cmd in cmds:
                                    stdout, stderr = _run_command(cmd)
                                if stdout.decode("utf-8") == "Hello, world!":
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """)

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code, "weight": 1.0,
                           "hidden": True
                           }]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
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
        user_answer = ("class Test {\n\tint square_num(int a)"
                       " {\n\treturn a*a;\n\t}\n}")
        assert_test_case = dedent("""
            class main
            {
                public static <E> void check(E expect, E result)
                {
                    if(result.equals(expect))
                    {
                        System.out.println("Correct:Output expected "+expect+
                                            " and got "+result);
                    }
                else
                {
                    System.out.println("Incorrect:Output expected "+expect+
                                        " but got "+result);
                    System.exit(1);
                }
                }
                public static void main(String arg[])
                {
                   Test t = new Test();
                   int result, input, output;
                   input = 0; output = 0;
                   result = t.square_num(input);
                   System.out.println("Input submitted to the function: "+
                                        input);
                   check(output, result);
                   input = 5; output = 25;
                   result = t.square_num(input);
                   System.out.println("Input submitted to the function: "+
                                        input);
                   check(output, result);
                   input = 6; output = 36;
                   result = t.square_num(input);
                   System.out.println("Input submitted to the function: "+
                                        input);
                   check(output, result);
                }
            }
            """)

        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                if "return a*a" in user_answer:
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
                    'language': 'java'
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
                             class Test
                             {public static void main(String[] args){
                             System.out.print("Hello, world!");
                             }}
                             """)

        hook_code_1 = dedent("""\
                            def check_answer(user_answer):
                                with open("Test.java", "w+") as f:
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
                                cmds = ["javac Test.java", "java Test"]
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
                                if ('System.out.print("Hello, world!");' in
                                    user_answer):
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
                    'language': 'java'
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
                             class Test
                             {public static void main(String[] args){
                             while(0==0)
                            {
                            System.out.print("a");}
                            }}""")

        hook_code = dedent("""\
                            def check_answer(user_answer):
                                with open("Test.java", "w+") as f:
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
                                cmds = ["javac Test.java", "java Test"]
                                for cmd in cmds:
                                    stdout, stderr = _run_command(cmd)
                                if stdout.decode("utf-8") == "Hello, world!":
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """)

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code, "weight": 1.0,
                           }]

        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'java'
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
