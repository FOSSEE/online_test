#!/usr/bin/env python
import traceback
import pwd
import os
from os.path import join, isfile
import subprocess
import importlib

# local imports
from code_evaluator import CodeEvaluator


class CppCodeEvaluator(CodeEvaluator):
    """Tests the C code obtained from Code Server"""
    def setup(self):
        super(CppCodeEvaluator, self).setup()
        self.submit_code_path = self.create_submit_code_file('submit.c')

    def teardown(self):
        super(CppCodeEvaluator, self).teardown()
        # Delete the created file.
        os.remove(self.submit_code_path) 

    def set_file_paths(self):
        user_output_path = os.getcwd() + '/output'
        ref_output_path = os.getcwd() + '/executable'

        return user_output_path, ref_output_path

    def get_commands(self, clean_ref_code_path, user_output_path,
                                 ref_output_path):
        compile_command = 'g++  {0} -c -o {1}'.format(self.submit_code_path,
                                                 user_output_path)
        compile_main = 'g++ {0} {1} -o {2}'.format(clean_ref_code_path,
                                                user_output_path,
                                                ref_output_path)
        return compile_command, compile_main

    def check_code(self, user_answer, test_case_data):
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
            ref_code_path = test_case_data[0]
            clean_ref_code_path, clean_test_case_path = self._set_test_code_file_path(ref_code_path)

            if not isfile(clean_ref_code_path):
                return False, "No file at %s or Incorrect path" % clean_ref_code_path
            if not isfile(self.submit_code_path):
                return False, 'No file at %s or Incorrect path' % self.submit_code_path

            success = False
            self.write_to_submit_code_file(self.submit_code_path, user_answer)
            user_output_path, ref_output_path = self.set_file_paths()
            compile_command, compile_main = self.get_commands(clean_ref_code_path, user_output_path, ref_output_path)
            ret = self._compile_command(compile_command)
            proc, stdnt_stderr = ret
            stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)

            # Only if compilation is successful, the program is executed
            # And tested with testcases
            if stdnt_stderr == '':
                ret = self._compile_command(compile_main)
                proc, main_err = ret
                main_err = self._remove_null_substitute_char(main_err)

                if main_err == '':
                    ret = self._run_command([ref_output_path], stdin=None,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                    proc, stdout, stderr = ret
                    if proc.returncode == 0:
                        success, err = True, "Correct answer"
                    else:
                        err = stdout + "\n" + stderr
                    os.remove(ref_output_path)
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
                os.remove(user_output_path)
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

    # def __init__(self, test_case_data, test, language, user_answer,
    #                  ref_code_path=None, in_dir=None):
    #     super(CppCodeEvaluator, self).__init__(test_case_data, test, language,
    #                                              user_answer, ref_code_path,
    #                                              in_dir)
    #     self.test_case_args = self.setup()

    # def setup(self):
    #     super(CppCodeEvaluator, self).setup()

    #     get_ref_path = self.ref_code_path
    #     ref_path, test_case_path = self._set_test_code_file_path(get_ref_path)
    #     self.submit_path = self.create_submit_code_file('submit.c')

    #     # Set file paths #@@@ in different func get_output_file_paths
    #     c_user_output_path = os.getcwd() + '/output'
    #     c_ref_output_path = os.getcwd() + '/executable'

    #     # Set command variables #@@@ This section in different func get_commands
    #     compile_command = 'g++  {0} -c -o {1}'.format(self.submit_path,
    #                                              c_user_output_path)
    #     compile_main = 'g++ {0} {1} -o {2}'.format(ref_path,
    #                                             c_user_output_path,
    #                                             c_ref_output_path)
    #     run_command_args = [c_ref_output_path]
    #     remove_user_output = c_user_output_path #@@@ not required
    #     remove_ref_output = c_ref_output_path #@@@ not required

    #     return (ref_path, self.submit_path, compile_command, compile_main,
    #              run_command_args, remove_user_output, remove_ref_output)

    # def check_code(self, ref_code_path, submit_code_path, compile_command,
    #                  compile_main, run_command_args, remove_user_output,
    #                  remove_ref_output):
    #     """ Function validates student code using instructor code as
    #     reference.The first argument ref_code_path, is the path to
    #     instructor code, it is assumed to have executable permission.
    #     The second argument submit_code_path, is the path to the student
    #     code, it is assumed to have executable permission.

    #     Returns
    #     --------

    #     returns (True, "Correct answer") : If the student function returns
    #     expected output when called by reference code.

    #     returns (False, error_msg): If the student function fails to return
    #     expected output when called by reference code.

    #     Returns (False, error_msg): If mandatory arguments are not files or
    #     if the required permissions are not given to the file(s).

    #     """
    #     if not isfile(ref_code_path):
    #         return False, "No file at %s or Incorrect path" % ref_code_path
    #     if not isfile(submit_code_path):
    #         return False, 'No file at %s or Incorrect path' % submit_code_path

    #     success = False
    #     ret = self._compile_command(compile_command)
    #     proc, stdnt_stderr = ret
    #     stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)

    #     # Only if compilation is successful, the program is executed
    #     # And tested with testcases
    #     if stdnt_stderr == '':
    #         ret = self._compile_command(compile_main)
    #         proc, main_err = ret
    #         main_err = self._remove_null_substitute_char(main_err)

    #         if main_err == '':
    #             ret = self._run_command(run_command_args, stdin=None,
    #                                     stdout=subprocess.PIPE,
    #                                     stderr=subprocess.PIPE)
    #             proc, stdout, stderr = ret
    #             if proc.returncode == 0:
    #                 success, err = True, "Correct answer"
    #             else:
    #                 err = stdout + "\n" + stderr
    #             os.remove(remove_ref_output)
    #         else:
    #             err = "Error:"
    #             try:
    #                 error_lines = main_err.splitlines()
    #                 for e in error_lines:
    #                     if ':' in e:
    #                         err = err + "\n" + e.split(":", 1)[1]
    #                     else:
    #                         err = err + "\n" + e
    #             except:
    #                     err = err + "\n" + main_err
    #         os.remove(remove_user_output)
    #     else:
    #         err = "Compilation Error:"
    #         try:
    #             error_lines = stdnt_stderr.splitlines()
    #             for e in error_lines:
    #                 if ':' in e:
    #                     err = err + "\n" + e.split(":", 1)[1]
    #                 else:
    #                     err = err + "\n" + e
    #         except:
    #             err = err + "\n" + stdnt_stderr

    #     return success, err
