import unittest
import os
from exam.scilab_code_evaluator import ScilabCodeEvaluator
from exam.settings import SERVER_TIMEOUT

class ScilabEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.language = "scilab"
        self.ref_code_path = "scilab_files/test_add.sce"
        self.in_dir = "/tmp"
        self.test_case_data = []
        self.test = None

    def test_correct_answer(self):
        user_answer = "funcprot(0)\nfunction[c]=add(a,b)\n\tc=a+b;\nendfunction"
        get_class = ScilabCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_correct_answer_2(self):
        user_answer = "funcprot(0)\nfunction[c]=add(a,b)\n\tc=a-b;\nendfunction"
        get_class = ScilabCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("error"), "Correct answer")

    def test_error(self):
        user_answer = "funcprot(0)\nfunction[c]=add(a,b)\n\t   c=a+b;\ndis(\tendfunction"
        get_class = ScilabCodeEvaluator(self.test_case_data, self.test, self.language, user_answer, self.ref_code_path, self.in_dir)
        result = get_class.evaluate()
 
        self.assertFalse(result.get("success"))
        self.assertTrue("Error" in result.get("error"))

if __name__ == '__main__':
    unittest.main()