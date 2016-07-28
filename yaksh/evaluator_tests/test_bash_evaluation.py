import unittest
import os
from yaksh.bash_code_evaluator import BashCodeEvaluator
from yaksh.settings import SERVER_TIMEOUT

class BashEvaluationTestCases(unittest.TestCase):
    def setUp(self):
        self.test_case_data = [
            {"test_case": "bash_files/sample.sh,bash_files/sample.args"}
        ]
        self.in_dir = os.getcwd()
        self.timeout_msg = ("Code took more than {0} seconds to run. "
            "You probably have an infinite loop in your"
            " code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def test_correct_answer(self):
        user_answer = ("#!/bin/bash\n[[ $# -eq 2 ]]"
            " && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))"
        )
        get_class = BashCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get('success'))
        self.assertEquals(result.get('error'), "Correct answer")

    def test_error(self):
        user_answer = ("#!/bin/bash\n[[ $# -eq 2 ]] "
            "&& echo $(( $1 - $2 )) && exit $(( $1 - $2 ))")
        get_class = BashCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertTrue("Error" in result.get("error"))

    def test_infinite_loop(self):
        user_answer = ("#!/bin/bash\nwhile [ 1 ] ;"
            " do echo "" > /dev/null ; done")
        get_class = BashCodeEvaluator(self.in_dir)
        kwargs = {'user_answer': user_answer, 
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertFalse(result.get("success"))
        self.assertEquals(result.get("error"), self.timeout_msg)

    def test_file_based_assert(self):
        self.file_paths = [(os.getcwd()+"/yaksh/test.txt", False)]
        self.test_case_data = [
            {"test_case": "bash_files/sample1.sh,bash_files/sample1.args"}
        ]
        user_answer = ("#!/bin/bash\ncat $1")
        get_class = BashCodeEvaluator()
        kwargs = {'user_answer': user_answer,
                    'test_case_data': self.test_case_data,
                    'file_paths': self.file_paths
                }
        result = get_class.evaluate(**kwargs)
        self.assertTrue(result.get("success"))
        self.assertEquals(result.get("error"), "Correct answer")

if __name__ == '__main__':
    unittest.main()
