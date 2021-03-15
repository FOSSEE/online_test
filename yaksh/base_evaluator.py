#!/usr/bin/env python
from __future__ import unicode_literals
import os
from os.path import abspath, exists
import subprocess
import stat
import signal


# Local imports
from .grader import TimeoutException


class BaseEvaluator(object):
    """Base Evaluator class containing generic attributes
        and callable methods"""

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
            proc = subprocess.Popen(cmd_args,
                                    preexec_fn=os.setpgrp, *args, **kw)
            stdout, stderr = proc.communicate()
        except TimeoutException:
            # Runaway code, so kill it.
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            # Re-raise exception.
            raise
        return proc, stdout.decode('utf-8'), stderr.decode('utf-8')

    def _remove_null_substitute_char(self, string):
        """Returns a string without any null and substitute characters"""
        stripped = ""
        for c in string:
            if ord(c) != 26 and ord(c) != 0:
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

    def _set_file_as_executable(self, fname):
        os.chmod(fname, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                 stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH |
                 stat.S_IWOTH | stat.S_IXOTH)
