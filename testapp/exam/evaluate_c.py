#!/usr/bin/env python
import traceback
import pwd
import os
from os.path import join, isfile
import subprocess
import importlib

# local imports
from code_server import TestCode
from registry import registry


class EvaluateC(TestCode):
    """Tests the C code obtained from Code Server"""
    def evaluate_code(self):
        submit_path = self._create_submit_code_file('submit.c')
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

    def check_code(self, ref_code_path, submit_code_path, compile_command,
                     compile_main, run_command_args, remove_user_output,
                     remove_ref_output):
        """ Function validates student code using instructor code as
        reference.The first argument ref_code_path, is the path to
        instructor code, it is assumed to have executable permission.
        The second argument submit_code_path, is the path to the student
        code, it is assumed to have executable permission.

        Returns
        --------

        returns (True, "Correct answer") : If the student function returns
        expected output when called by reference code.

        returns (False, error_msg): If the student function fails to return
        expected output when called by reference code.

        Returns (False, error_msg): If mandatory arguments are not files or
        if the required permissions are not given to the file(s).

        """

        if not isfile(ref_code_path):
            return False, "No file at %s or Incorrect path" % ref_code_path
        if not isfile(submit_code_path):
            return False, 'No file at %s or Incorrect path' % submit_code_path

        success = False
        # output_path = os.getcwd() + '/output'
        ret = self._compile_command(compile_command)
        proc, stdnt_stderr = ret
        # if self.language == "java":
        stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)

        # Only if compilation is successful, the program is executed
        # And tested with testcases
        if stdnt_stderr == '':
            ret = self._compile_command(compile_main)
            proc, main_err = ret
            # if self.language == "java":
            # main_err = self._remove_null_substitute_char(main_err)

            if main_err == '':
                ret = self._run_command(run_command_args, stdin=None,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                proc, stdout, stderr = ret
                if proc.returncode == 0:
                    success, err = True, "Correct answer"
                else:
                    err = stdout + "\n" + stderr
                os.remove(remove_ref_output)
            else:
                err = "Error:"
                try:
                    error_lines = main_err.splitlines()
                    for e in error_lines:
                        if ':' in e:
                            err = err + "\n" + e.split(":", 1)[1]
                        else:
                            err = err + "\n" + e
                except:
                        err = err + "\n" + main_err
            os.remove(remove_user_output)
        else:
            err = "Compilation Error:"
            try:
                error_lines = stdnt_stderr.splitlines()
                for e in error_lines:
                    if ':' in e:
                        err = err + "\n" + e.split(":", 1)[1]
                    else:
                        err = err + "\n" + e
            except:
                err = err + "\n" + stdnt_stderr

        return success, err

    def _remove_null_substitute_char(self, string):
        """Returns a string without any null and substitute characters"""
        stripped = ""
        for c in string:
            if ord(c) is not 26 and ord(c) is not 0:
                stripped = stripped + c
        return ''.join(stripped)

registry.register('c', evaluate_c, EvaluateC)