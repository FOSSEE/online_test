#!/usr/bin/env python
import traceback
import os
from os.path import join, isfile
import subprocess
import re
import importlib

# local imports
from evaluate_code import EvaluateCode
from language_registry import registry


class EvaluateScilabCode(EvaluateCode):
    """Tests the Scilab code obtained from Code Server"""
    # Public Protocol ##########
    def evaluate_code(self):
        submit_path = self.create_submit_code_file('function.sci')
        ref_path, test_case_path = self.set_test_code_file_path()
        success = False

        cmd = 'printf "lines(0)\nexec(\'{0}\',2);\nquit();"'.format(ref_path)
        cmd += ' | timeout 8 scilab-cli -nb'
        ret = self.run_command(cmd,
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

        # Delete the created file.
        os.remove(submit_path)

        return success, err

    # Private Protocol ##########
    def _remove_scilab_exit(self, string):
        """
            Removes exit, quit and abort from the scilab code
        """
        new_string = ""
        i = 0
        for line in string.splitlines():
            new_line = re.sub(r"exit.*$", "", line)
            new_line = re.sub(r"quit.*$", "", new_line)
            new_line = re.sub(r"abort.*$", "", new_line)
            if line != new_line:
                i = i + 1
            new_string = new_string + '\n' + new_line
        return new_string, i

    # Private Protocol ##########
    def _get_error(self, string):
        """
            Fetches only the error from the string.
            Returns None if no error.
        """
        obj = re.search("!.+\n.+", string)
        if obj:
            return obj.group()
        return None

    # Private Protocol ##########
    def _strip_output(self, out):
        """
            Cleans whitespace from the output
        """
        strip_out = "Message"
        for l in out.split('\n'):
            if l.strip():
                strip_out = strip_out+"\n"+l.strip()
        return strip_out


registry.register('scilab', EvaluateScilabCode)
