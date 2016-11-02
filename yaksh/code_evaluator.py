#!/usr/bin/env python
from __future__ import unicode_literals
import sys
import pwd
import os
import stat
from os.path import isdir, dirname, abspath, join, isfile, exists
import signal
import traceback
from multiprocessing import Process, Queue
import subprocess
import re

try:
    from SimpleXMLRPCServer import SimpleXMLRPCServer
except ImportError:
    # The above import will not work on Python-3.x.
    from xmlrpc.server import SimpleXMLRPCServer

# Local imports
from .settings import SERVER_TIMEOUT

MY_DIR = abspath(dirname(__file__))


# Raised when the code times-out.
# c.f. http://pguides.net/python/timeout-a-function
class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    """A handler for the ALARM signal."""
    raise TimeoutException('Code took too long to run.')


def create_signal_handler():
    """Add a new signal handler for the execution of this code."""
    prev_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(SERVER_TIMEOUT)
    return prev_handler


def set_original_signal_handler(old_handler=None):
    """Set back any original signal handler."""
    if old_handler is not None:
        signal.signal(signal.SIGALRM, old_handler)
        return
    else:
        raise Exception("Signal Handler: object cannot be NoneType")


def delete_signal_handler():
    signal.alarm(0)
    return


class CodeEvaluator(object):
    """Tests the code obtained from Code Server"""
    def __init__(self, in_dir=None):
        msg = 'Code took more than %s seconds to run. You probably '\
              'have an infinite loop in your code.' % SERVER_TIMEOUT
        self.timeout_msg = msg
        self.in_dir = in_dir

    def evaluate(self, **kwargs):
        """Evaluates given code with the test cases based on
        given arguments in test_case_data.

        The ref_code_path is a path to the reference code.
        The reference code will call the function submitted by the student.
        The reference code will check for the expected output.

        If the path's start with a "/" then we assume they are absolute paths.
        If not, we assume they are relative paths w.r.t. the location of this
        code_server script.

        If the optional `in_dir` keyword argument is supplied it changes the
        directory to that directory (it does not change it back to the original
        when done).

        Returns
        -------

        A tuple: (success, error message, marks).
        """

        self.setup()
        success, error, marks = self.safe_evaluate(**kwargs)
        self.teardown()

        result = {'success': success, 'error': error, 'marks': marks}
        return result

    # Private Protocol ##########
    def setup(self):
        if self.in_dir:
            if not os.path.exists(self.in_dir):
                os.makedirs(self.in_dir)
        self._change_dir(self.in_dir)

    def safe_evaluate(self, user_answer, partial_grading, test_case_data, file_paths=None):
        """
        Handles code evaluation along with compilation, signal handling
        and Exception handling
        """

        # Add a new signal handler for the execution of this code.
        prev_handler = create_signal_handler()
        success = False
        error = ""
        marks = 0.0

        # Do whatever testing needed.
        try:
            for test_case in test_case_data:
                success = False
                self.compile_code(user_answer, file_paths, **test_case)
                success, err, test_case_marks = self.check_code(user_answer,
                    file_paths,
                    partial_grading,
                    **test_case
                )
                if success:
                    marks += test_case_marks
                else:
                    error += err + "\n"

        except TimeoutException:
            error = self.timeout_msg
        except OSError:
            msg = traceback.format_exc(limit=0)
            error = "Error: {0}".format(msg)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_list = traceback.format_exception(exc_type, exc_value, exc_tb)
            if len(tb_list) > 2:
                del tb_list[1:3]
            error = "Error: {0}".format("".join(tb_list))
        finally:
            # Set back any original signal handler.
            set_original_signal_handler(prev_handler)

        return success, error, marks

    def teardown(self):
        # Cancel the signal
        delete_signal_handler()
        self._change_dir(dirname(MY_DIR))

    def check_code(self):
        raise NotImplementedError("check_code method not implemented")

    def compile_code(self, user_answer, file_paths, **kwargs):
        pass

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
        os.chmod(fname,  stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
                 | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
                 | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)

    def _set_test_code_file_path(self, ref_path=None, test_case_path=None):
        if ref_path and not ref_path.startswith('/'):
            ref_path = join(MY_DIR, ref_path)

        if test_case_path and not test_case_path.startswith('/'):
            test_case_path = join(MY_DIR, test_case_path)

        return ref_path, test_case_path

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

    def _change_dir(self, in_dir):
        if in_dir is not None and isdir(in_dir):
            os.chdir(in_dir)

    def _remove_null_substitute_char(self, string):
        """Returns a string without any null and substitute characters"""
        stripped = ""
        for c in string:
            if ord(c) is not 26 and ord(c) is not 0:
                stripped = stripped + c
        return ''.join(stripped)
