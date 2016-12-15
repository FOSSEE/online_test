#!/usr/bin/env python
from __future__ import unicode_literals
import traceback
import pwd
import os
from os.path import join, isfile
import subprocess

class BaseEvaluator(object):
    """Base Evaluator class containing generic attributes and callable methods"""

    def __init__(self):
        pass

    def check_code(self):
        raise NotImplementedError("check_code method not implemented")

    def compile_code(self):
        pass

    def _run_command(self, cmd_args, *args, **kw):
        """Run a command in a subprocess while blocking, the process is killed
        if it takes more than 2 seconds to run.  Return the Popen object, the
        stdout and stderr.
        """
        try:
            proc = subprocess.Popen(cmd_args, *args, **kw)
            stdout, stderr = proc.communicate()
        except TimeoutException:
            # Runaway code, so kill it.
            proc.kill()
            # Re-raise exception.
            raise
        return proc, stdout.decode('utf-8'), stderr.decode('utf-8')

    def _remove_null_substitute_char(self, string):
        """Returns a string without any null and substitute characters"""
        stripped = ""
        for c in string:
            if ord(c) is not 26 and ord(c) is not 0:
                stripped = stripped + c
        return ''.join(stripped)

    def create_submit_code_file(self, file_name):
        """ Set the file path for code (`answer`)"""
        submit_path = abspath(file_name)
        if not exists(submit_path):
            submit_f = open(submit_path, 'w')
            submit_f.close()

        return submit_path

    def write_to_submit_code_file(self, file_path, user_answer):
        """ Write the code (`answer`) to a file"""
        submit_f = open(file_path, 'w')
        submit_f.write(user_answer.lstrip())
        submit_f.close()

    def _set_test_code_file_path(self, ref_path=None, test_case_path=None):
        if ref_path and not ref_path.startswith('/'):
            ref_path = join(MY_DIR, ref_path)

        if test_case_path and not test_case_path.startswith('/'):
            test_case_path = join(MY_DIR, test_case_path)

        return ref_path, test_case_path
