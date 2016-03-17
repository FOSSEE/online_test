import unittest
import os
from yaksh import code_evaluator as evaluator
from yaksh.scilab_code_evaluator import ScilabCodeEvaluator
from yaksh.settings import SERVER_TIMEOUT

class ScilabEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.test_case_data = [{"test_case": "scilab_files/test_add.sce"}]
        self.in_dir = "/tmp"
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in your code.").format(SERVER_TIMEOUT)

    def test_correct_answer(self):
        user_answer = "funcprot(0)\nfunction[c]=add(a,b)\n\tc=a+b;\nendfunction"
        get_class = ScilabCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertEquals(result.get('error'), "Correct answer")
        self.assertTrue(result.get('success'))

    def test_error(self):
        user_answer = "funcprot(0)\nfunction[c]=add(a,b)\n\tc=a+b;\ndis(\tendfunction"
        get_class = ScilabCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs) 
        self.assertFalse(result.get("success"))
        self.assertTrue("error" in result.get("error"))


    def test_incorrect_answer(self):
        user_answer = "funcprot(0)\nfunction[c]=add(a,b)\n\tc=a-b;\nendfunction"
        get_class = ScilabCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get('success'))
        self.assertIn("Message", result.get('error'))
        self.assertTrue(result.get('error').splitlines > 1)

    def test_infinite_loop(self):
        user_answer = "funcprot(0)\nfunction[c]=add(a,b)\n\tc=a;\nwhile(1==1)\nend\nendfunction"
        get_class = ScilabCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data
                }
        result = get_class.evaluate(**kwargs) 
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)

if __name__ == '__main__':
    unittest.main()
