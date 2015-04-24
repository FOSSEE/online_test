#!/usr/bin/env python
import traceback
import pwd
import os
from os.path import join, isfile
import subprocess
import importlib

# local imports
from evaluate_c_code import EvaluateCCode
from evaluate_code import EvaluateCode
from language_registry import registry


class EvaluateJavaCode(EvaluateCCode, EvaluateCode):
    """Tests the C code obtained from Code Server"""
    ## Public Protocol ##########
    def evaluate_code(self):
        submit_path = self.create_submit_code_file('Test.java')
        ref_path, test_case_path = self.set_test_code_file_path(self.ref_code_path)
        success = False

        # Set file paths
        java_student_directory = os.getcwd() + '/'
        java_ref_file_name = (ref_path.split('/')[-1]) #.split('.')[0]

        # Set command variables
        compile_command = 'javac  {0}'.format(submit_path),
        compile_main = 'javac {0} -classpath {1} -d {2}'.format(ref_path,
                                                                 java_student_directory,
                                                                 java_student_directory)
        run_command_args = "java -cp {0} {1}".format(java_student_directory,
                                                     java_ref_file_name)
        remove_user_output = "{0}{1}.class".format(java_student_directory,
                                                     'Test')
        remove_ref_output = "{0}{1}.class".format(java_student_directory,
                                                     java_ref_file_name)

        success, err = self.check_code(ref_path, submit_path, compile_command,
                                     compile_main, run_command_args,
                                     remove_user_output, remove_ref_output)

        # Delete the created file.
        os.remove(submit_path)

        return success, err


registry.register('java', EvaluateJavaCode)