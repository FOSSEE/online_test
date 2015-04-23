import sys
from SimpleXMLRPCServer import SimpleXMLRPCServer
import pwd
import os
import stat
from os.path import isdir, dirname, abspath, join, isfile
import signal
from multiprocessing import Process, Queue
import subprocess
import re
import json
import importlib
# Local imports.
from settings import SERVER_PORTS, SERVER_TIMEOUT, SERVER_POOL_PORT


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



###############################################################################
# `TestCode` class.
###############################################################################
class TestCode(object):
    """Tests the code obtained from Code Server"""
    def __init__(self, test_parameter, language, user_answer, ref_code_path=None, in_dir=None):
        msg = 'Code took more than %s seconds to run. You probably '\
              'have an infinite loop in your code.' % SERVER_TIMEOUT
        self.timeout_msg = msg
        self.test_parameter = test_parameter
        self.language = language.lower()
        self.user_answer = user_answer
        self.ref_code_path = ref_code_path
        self.in_dir = in_dir

    @classmethod
    def from_json(cls, blob, language, in_dir):
        info_parameter = json.loads(blob)
        test_parameter = info_parameter.get("test_parameter")
        user_answer = info_parameter.get("user_answer")
        ref_code_path = info_parameter.get("ref_code_path")

        instance = cls(test_parameter, language, user_answer, ref_code_path, in_dir)
        return instance

    def run_code(self):
        """Tests given code  (`answer`) with the test cases based on
        given arguments.

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

        A tuple: (success, error message).
        """
        self._change_dir(self.in_dir)

        # Add a new signal handler for the execution of this code.
        prev_handler = create_signal_handler()
        success = False

        # Do whatever testing needed.
        try:
            success, err = self.evaluate_code()

        except TimeoutException:
            err = self.timeout_msg
        except:
            type, value = sys.exc_info()[:2]
            err = "Error: {0}".format(repr(value))
        finally:
            # Set back any original signal handler.
            set_original_signal_handler(prev_handler)

        # Cancel the signal
        delete_signal_handler()

        result = {'success': success, 'error': err}
        return result

    def evaluate_code(self):
        raise NotImplementedError("evaluate_code method not implemented")

    def create_submit_code_file(self, file_name):
        """ Write the code (`answer`) to a file and set the file path"""
        # File name/extension depending on the question language
        submit_f = open(file_name, 'w')
        submit_f.write(self.user_answer.lstrip())
        submit_f.close()
        submit_path = abspath(submit_f.name)            

        return submit_path

    def set_file_as_executable(self, fname):
        os.chmod(fname,  stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
                 | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
                 | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)

    def set_test_code_file_path(self, ref_path=None, test_case_path=None):
        if ref_path and not ref_path.startswith('/'):
            ref_path = join(MY_DIR, ref_path)

        if test_case_path and not test_case_path.startswith('/'):
            test_case_path = join(MY_DIR, test_case_path)

        return ref_path, test_case_path

    def run_command(self, cmd_args, *args, **kw):
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
        return proc, stdout, stderr

    def compile_command(self, cmd, *args, **kw):
        """Compiles C/C++/java code and returns errors if any.
        Run a command in a subprocess while blocking, the process is killed
        if it takes more than 2 seconds to run.  Return the Popen object, the
        stderr.
        """
        try:
            proc_compile = subprocess.Popen(cmd, shell=True, stdin=None,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
            out, err = proc_compile.communicate()
        except TimeoutException:
            # Runaway code, so kill it.
            proc_compile.kill()
            # Re-raise exception.
            raise
        return proc_compile, err

    def _change_dir(self, in_dir):
        if in_dir is not None and isdir(in_dir):
            os.chdir(in_dir)