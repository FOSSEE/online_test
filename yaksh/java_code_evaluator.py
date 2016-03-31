#!/usr/bin/env python
import traceback
import pwd
import os
from os.path import join, isfile
import subprocess
import importlib

# local imports
from code_evaluator import CodeEvaluator


class JavaCodeEvaluator(CodeEvaluator):
    """Tests the Java code obtained from Code Server"""
    def setup(self):
        super(JavaCodeEvaluator, self).setup()
        self.submit_code_path = self.create_submit_code_file('Test.java')

    def teardown(self):
        super(JavaCodeEvaluator, self).teardown()
        # Delete the created file.
        os.remove(self.submit_code_path) 

    def get_commands(self, clean_ref_code_path, user_code_directory):
        compile_command = 'javac  {0}'.format(self.submit_code_path),
        compile_main = ('javac {0} -classpath '
                        '{1} -d {2}').format(clean_ref_code_path,
                                             user_code_directory,
                                             user_code_directory)
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
        user_code_directory = os.getcwd() + '/'
        self.write_to_submit_code_file(self.submit_code_path, user_answer)
        ref_file_name = (clean_ref_code_path.split('/')[-1]).split('.')[0]
        user_output_path = "{0}{1}.class".format(user_code_directory,
                                                     'Test')
        ref_output_path = "{0}{1}.class".format(user_code_directory,
                                                     ref_file_name)
        # user_output_path, ref_output_path = self.set_file_paths(user_code_directory, clean_ref_code_path)
        compile_command, compile_main = self.get_commands(clean_ref_code_path, user_code_directory)
        run_command_args = "java -cp {0} {1}".format(user_code_directory,
                                                     ref_file_name)
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
                ret = self._run_command(run_command_args, shell=True,
                                         stdin=None,
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
