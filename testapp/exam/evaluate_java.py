#!/usr/bin/env python
import traceback
import pwd
import os
from os.path import join, isfile
import subprocess
import importlib

# local imports
from evaluate_c import EvaluateC
from code_server import TestCode
from registry import registry



class EvaluateJava(EvaluateC, TestCode):
    """Tests the C code obtained from Code Server"""
    def evaluate_code(self):
        submit_path = self._create_submit_code_file('Test.java')
        get_ref_path = self.ref_code_path
        ref_path, test_case_path = self._set_test_code_file_path(get_ref_path)
        success = False

        # Set file paths
        java_student_directory = os.getcwd() + '/'
        java_ref_file_name = (ref_code_path.split('/')[-1]).split('.')[0],

        # Set command variables
        compile_command = 'javac  {0}'.format(submit_code_path),
        compile_main = 'javac {0} -classpath {1} -d {2}'.format(ref_code_path,
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

registry.register('java', evaluate_java, EvaluateJava)