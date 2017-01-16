#!/usr/bin/env python
from __future__ import unicode_literals
import sys
import pwd
import os
import stat
import contextlib
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
from .language_registry import create_evaluator_instance


MY_DIR = abspath(dirname(__file__))
registry = None

# Raised when the code times-out.
# c.f. http://pguides.net/python/timeout-a-function
class TimeoutException(Exception):
    pass

@contextlib.contextmanager
def change_dir(path):
    cur_dir = abspath(dirname(MY_DIR))
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cur_dir)


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


class Grader(object):
    """Tests the code obtained from Code Server"""
    def __init__(self, in_dir=None):
        msg = 'Code took more than %s seconds to run. You probably '\
              'have an infinite loop in your code.' % SERVER_TIMEOUT
        self.timeout_msg = msg
        self.in_dir = in_dir if in_dir else MY_DIR


    def evaluate(self, kwargs):
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

        A tuple: (success, error, weight).
        """
        self.setup()
        test_case_instances = self.get_evaluator_objects(kwargs)
        with change_dir(self.in_dir):
            success, error, weight = self.safe_evaluate(test_case_instances)
        self.teardown()

        result = {'success': success, 'error': error, 'weight': weight}
        return result

    # Private Protocol ##########
    def setup(self):
        if self.in_dir:
            if not os.path.exists(self.in_dir):
                os.makedirs(self.in_dir)

    def get_evaluator_objects(self, kwargs):
        metadata = kwargs.get('metadata')
        test_case_data = kwargs.get('test_case_data')
        test_case_instances = []

        for test_case in test_case_data:
            test_case_instance = create_evaluator_instance(metadata, test_case)
            test_case_instances.append(test_case_instance)
        return test_case_instances


    def safe_evaluate(self, test_case_instances):
        """
        Handles code evaluation along with compilation, signal handling
        and Exception handling
        """
        # Add a new signal handler for the execution of this code.
        prev_handler = create_signal_handler()
        success = False
        test_case_success_status = [False] * len(test_case_instances)
        error = []
        weight = 0.0

        # Do whatever testing needed.
        try:
            # Run evaluator selection registry here
            for idx, test_case_instance in enumerate(test_case_instances):
                test_case_success = False
                test_case_instance.compile_code()
                test_case_success, err, mark_fraction = test_case_instance.check_code()
                if test_case_success:
                    weight += mark_fraction * test_case_instance.weight
                else:
                    error.append(err)
                test_case_success_status[idx] = test_case_success

            success = all(test_case_success_status)

            for test_case_instance in test_case_instances:
                test_case_instance.teardown()

        except TimeoutException:
            error.append(self.timeout_msg)
        except OSError:
            msg = traceback.format_exc(limit=0)
            error.append("Error: {0}".format(msg))
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_list = traceback.format_exception(exc_type, exc_value, exc_tb)
            if len(tb_list) > 2:
                del tb_list[1:3]
            error.append("Error: {0}".format("".join(tb_list)))
        finally:
            # Set back any original signal handler.
            set_original_signal_handler(prev_handler)

        return success, error, weight

    def teardown(self):
        # Cancel the signal
        delete_signal_handler()
