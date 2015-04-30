import unittest
import os
# from exam import evaluate_c_code, evaluate_cpp_code, evaluate_java_code, evaluate_python_code, evaluate_scilab_code, evaluate_bash_code
from exam import c_cpp_code_evaluator, bash_code_evaluator, python_code_evaluator, scilab_code_evaluator, java_code_evaluator
from exam.language_registry import set_registry, get_registry
from exam.settings import SERVER_TIMEOUT


class RegistryTestCase(unittest.TestCase):
    def setUp(self):
        set_registry()
        self.registry_object = get_registry()

    def test_set_register(self):
        self.registry_object.register("demo_language", "demo_object")
        self.assertEquals(self.registry_object._registry["demo_language"], "demo_object")

    def test_get_class(self):
        self.test_set_register()
        cls = self.registry_object.get_class("demo_language")
        self.assertEquals(cls, "demo_object")

    def tearDown(self):
        self.registry_object = None


###############################################################################    
class PythonEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "Python"
        self.test_case_data = [{"func_name": "add", 
                                 "expected_answer": "5", 
                                 "test_id": u'null', 
                                 "pos_args": ["3", "2"], 
                                 "kw_args": {}
                                }]
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        user_answer = "def add(a, b):\n\treturn a + b"""
        get_class = python_code_evaluator.PythonCodeEvaluator(self.test_case_data, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = get_class.code_evaluator()
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "def add(a, b):\n\treturn a - b"
        test_case_data = [{"func_name": "add", 
                                 "expected_answer": "5", 
                                 "test_id": u'null', 
                                 "pos_args": ["3", "2"], 
                                 "kw_args": {}
                                }]
        get_class = python_code_evaluator.PythonCodeEvaluator(self.test_case_data, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = get_class.code_evaluator()
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), "AssertionError  in: assert add(3, 2) == 5")

    def test_infinite_loop(self):
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"""
        test_case_data = [{"func_name": "add", 
                                 "expected_answer": "5", 
                                 "test_id": u'null', 
                                 "pos_args": ["3", "2"], 
                                 "kw_args": {}
                                }]
        get_class = python_code_evaluator.PythonCodeEvaluator(self.test_case_data, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = get_class.code_evaluator()
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)


###############################################################################
class CEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "C"
        self.ref_code_path = "c_cpp_files/main.cpp"
        self.in_dir = "/tmp"
        self.test_case_data = []
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)


    def test_correct_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b;}"
        get_class = c_cpp_code_evaluator.CCppCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_compilation_error(self):
        user_answer = "int add(int a, int b)\n{return a+b}"
        get_class = c_cpp_code_evaluator.CCppCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()

        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "int add(int a, int b)\n{while(1>0){}}"
        get_class = c_cpp_code_evaluator.CCppCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()
 
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)


###############################################################################
class CppEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "CPP"
        self.ref_code_path = "c_cpp_files/main.cpp"
        self.in_dir = "/tmp"
        self.test_case_data = []
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)


    def test_correct_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b;}"
        get_class = c_cpp_code_evaluator.CCppCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_compilation_error(self):
        user_answer = "int add(int a, int b)\n{return a+b}"
        get_class = c_cpp_code_evaluator.CCppCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()

        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "int add(int a, int b)\n{while(1>0){}}"
        get_class = c_cpp_code_evaluator.CCppCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()
 
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)


###############################################################################
class BashEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "bash"
        self.ref_code_path = "bash_files/sample.sh,bash_files/sample.args"
        self.in_dir = "/tmp"
        self.test_case_data = []
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        user_answer = "#!/bin/bash\n[[ $# -eq 2 ]] && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))"
        get_class = bash_code_evaluator.BashCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_error(self):
        user_answer = "#!/bin/bash\n[[ $# -eq 2 ]] && echo $(( $1 - $2 )) && exit $(( $1 - $2 ))"
        get_class = bash_code_evaluator.BashCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()

        self.assertFalse(result.get("success"))
        self.assertTrue("Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "#!/bin/bash\nwhile [ 1 ] ; do echo "" > /dev/null ; done"
        get_class = bash_code_evaluator.BashCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()

        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)


###############################################################################
class JavaEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "java"
        self.ref_code_path = "java_files/main_square.java"
        self.in_dir = "/tmp"
        self.test_case_data = []
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        user_answer = "class Test {\n\tint square_num(int a) {\n\treturn a*a;\n\t}\n}"
        get_class = evaluate_java_code.EvaluateJavaCode(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.run_code()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_error(self):
        user_answer = "class Test {\n\tint square_num(int a) {\n\treturn a*a"
        get_class = evaluate_java_code.EvaluateJavaCode(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.run_code()
 
        self.assertFalse(result.get("success"))
        self.assertTrue("Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = "class Test {\n\tint square_num(int a) {\n\t\twhile(0==0){\n\t\t}\n\t}\n}"
        get_class = evaluate_java_code.EvaluateJavaCode(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.run_code()
 
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)


###############################################################################
class ScilabEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "scilab"
        self.ref_code_path = "scilab_files/test_add.sce"
        self.in_dir = "/tmp"
        self.test_case_data = []

    def test_correct_answer(self):
        user_answer = "funcprot(0)\nfunction[c]=add(a,b)\n\tc=a+b;\nendfunction"
        get_class = scilab_code_evaluator.ScilabCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_correct_answer_2(self):
        user_answer = "funcprot(0)\nfunction[c]=add(a,b)\n\tc=a-b;\nendfunction"
        get_class = scilab_code_evaluator.ScilabCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_error(self):
        user_answer = "funcprot(0)\nfunction[c]=add(a,b)\n\t   c=a+b;\ndis(\tendfunction"
        get_class = scilab_code_evaluator.ScilabCodeEvaluator(self.test_case_data, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.code_evaluator()
 
        self.assertFalse(result.get("success"))
        self.assertTrue("Error" in result.get("error"))


if __name__ == '__main__':
    unittest.main()