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


class EvaluateCpp(EvaluateC, TestCode):
    """Tests the C code obtained from Code Server"""
    def evaluate_code(self):
        submit_path = self._create_submit_code_file('submitstd.cpp')
        get_ref_path = self.ref_code_path
        ref_path, test_case_path = self._set_test_code_file_path(get_ref_path)
        success = False

        # Set file paths
        c_user_output_path = os.getcwd() + '/output',
        c_ref_output_path = os.getcwd() + '/executable',

        # Set command variables
        compile_command = 'g++  {0} -c -o {1}'.format(submit_path,
                                                    c_user_output_path),
        compile_main = 'g++ {0} {1} -o {2}'.format(ref_path,
                                                c_user_output_path,
                                                c_ref_output_path),
        run_command_args = c_ref_output_path
        remove_user_output = c_user_output_path
        remove_ref_output = c_ref_output_path

        success, err = self.check_code(ref_path, submit_path, compile_command,
                                     compile_main, run_command_args,
                                     remove_user_output, remove_ref_output)

        # Delete the created file.
        os.remove(submit_path)

        return success, err
