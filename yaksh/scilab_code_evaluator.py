#!/usr/bin/env python
import traceback
import os
from os.path import join, isfile
import subprocess
import re
import importlib

# local imports
from code_evaluator import CodeEvaluator


class ScilabCodeEvaluator(CodeEvaluator):
    """Tests the Scilab code obtained from Code Server"""
    def __init__(self, test_case_data, test, language, user_answer,
                     ref_code_path=None, in_dir=None):
        super(ScilabCodeEvaluator, self).__init__(test_case_data, test,
                                                 language, user_answer,
                                                 ref_code_path, in_dir)

        # Removes all the commands that terminates scilab
        self.user_answer, self.terminate_commands = self._remove_scilab_exit(user_answer.lstrip())
        self.test_case_args = self.setup()

    def setup(self):
        super(ScilabCodeEvaluator, self).setup()

        ref_path, test_case_path = self._set_test_code_file_path(self.ref_code_path)
        self.submit_path = self.create_submit_code_file('function.sci')

        return ref_path, # Return as a tuple

    def teardown(self):
        # Delete the created file.
        super(ScilabCodeEvaluator, self).teardown()
        os.remove(self.submit_path)

    def check_code(self, ref_path):
        success = False

        # Throw message if there are commmands that terminates scilab
        add_err=""
        if self.terminate_commands:
            add_err = "Please do not use exit, quit and abort commands in your\
                        code.\n Otherwise your code will not be evaluated\
                        correctly.\n"

        cmd = 'printf "lines(0)\nexec(\'{0}\',2);\nquit();"'.format(ref_path)
        cmd += ' | timeout 8 scilab-cli -nb'
        ret = self._run_command(cmd,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc, stdout, stderr = ret

        # Get only the error.
        stderr = self._get_error(stdout)
        if stderr is None:
            # Clean output
            stdout = self._strip_output(stdout)
            if proc.returncode == 5:
                success, err = True, "Correct answer"
            else:
                err = add_err + stdout
        else:
            err = add_err + stderr

        return success, err

    def _remove_scilab_exit(self, string):
        """
            Removes exit, quit and abort from the scilab code
        """
        new_string = ""
        terminate_commands = False
        for line in string.splitlines():
            new_line = re.sub(r"exit.*$", "", line)
            new_line = re.sub(r"quit.*$", "", new_line)
            new_line = re.sub(r"abort.*$", "", new_line)
            if line != new_line:
                terminate_commands = True
            new_string = new_string + '\n' + new_line
        return new_string, terminate_commands

    def _get_error(self, string):
        """
            Fetches only the error from the string.
            Returns None if no error.
        """
        obj = re.search("!.+\n.+", string)
        if obj:
            return obj.group()
        return None

    def _strip_output(self, out):
        """
            Cleans whitespace from the output
        """
        strip_out = "Message"
        for l in out.split('\n'):
            if l.strip():
                strip_out = strip_out+"\n"+l.strip()
        return strip_out

