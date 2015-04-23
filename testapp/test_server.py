import unittest
import os
from exam import evaluate_c, evaluate_cpp, evaluate_bash, evaluate_python

class TestPythonEvaluation(unittest.TestCase):
    def setUp(self):
        self.language = "Python"
        self.test_parameter = [{"func_name": "add", 
                                 "expected_answer": "5", 
                                 "test_id": u'null', 
                                 "pos_args": ["3", "2"], 
                                 "kw_args": {}
                                }]
    def test_correct_answer(self):
        user_answer = "def add(a, b):\n\treturn a + b"""
        get_class = evaluate_python.EvaluatePython(self.test_parameter, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = get_class.run_code()
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "def add(a, b):\n\treturn a - b"
        test_parameter = [{"func_name": "add", 
                                 "expected_answer": "5", 
                                 "test_id": u'null', 
                                 "pos_args": ["3", "2"], 
                                 "kw_args": {}
                                }]
        get_class = evaluate_python.EvaluatePython(self.test_parameter, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = get_class.run_code()
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("error"), "AssertionError  in: assert add(3, 2) == 5")

    def test_infinite_loop(self):
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"""
        test_parameter = [{"func_name": "add", 
                                 "expected_answer": "5", 
                                 "test_id": u'null', 
                                 "pos_args": ["3", "2"], 
                                 "kw_args": {}
                                }]
        get_class = evaluate_python.EvaluatePython(self.test_parameter, self.language, user_answer, ref_code_path=None, in_dir=None)
        result = get_class.run_code()
        self.assertFalse(result.get("success"))
        self.assertTrue("Code took more than" in result.get("error"))

###############################################################################
class TestCEvaluation(unittest.TestCase):
    def setUp(self):
        self.language = "C"
        self.ref_code_path = "c_cpp_files/main.cpp"
        self.in_dir = "/tmp"
        self.test_parameter = []

    def test_correct_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b;}"
        get_class = evaluate_c.EvaluateC(self.test_parameter, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.run_code()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b}"
        get_class = evaluate_c.EvaluateC(self.test_parameter, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.run_code()

        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

###############################################################################
class TestCPPEvaluation(unittest.TestCase):
    def setUp(self):
        self.language = "CPP"
        self.ref_code_path = "c_cpp_files/main.cpp"
        self.in_dir = "/tmp"
        self.test_parameter = []

    def test_correct_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b;}"
        get_class = evaluate_cpp.EvaluateCpp(self.test_parameter, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.run_code()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_incorrect_answer(self):
        user_answer = "int add(int a, int b)\n{return a+b}"
        get_class = evaluate_cpp.EvaluateCpp(self.test_parameter, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.run_code()
        error_msg =  ""

        self.assertFalse(result.get("success"))
        self.assertTrue("Compilation Error" in result.get("error"))

if __name__ == '__main__':
    unittest.main()