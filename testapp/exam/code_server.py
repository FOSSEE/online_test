#!/usr/bin/env python
"""This server runs an XMLRPC server that can be submitted code and tests
and returns the output.  It *should* be run as root and will run as the user
'nobody' so as to minimize any damange by errant code.  This can be configured
by editing settings.py to run as many servers as desired.  One can also
specify the ports on the command line.  Here are examples::

  $ sudo ./code_server.py
  # Runs servers based on settings.py:SERVER_PORTS one server per port given.

or::

  $ sudo ./code_server.py 8001 8002 8003 8004 8005
  # Runs 5 servers on ports specified.

All these servers should be running as nobody.  This will also start a server
pool that defaults to port 50000 and is configurable in
settings.py:SERVER_POOL_PORT.  This port exposes a `get_server_port` function
that returns an available server.
"""
import sys
import traceback
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
from registry import registry


MY_DIR = abspath(dirname(__file__))

registry.register('python', )
registry.register('py', MyTestCode)

def run_as_nobody():
    """Runs the current process as nobody."""
    # Set the effective uid and to that of nobody.
    nobody = pwd.getpwnam('nobody')
    os.setegid(nobody.pw_gid)
    os.seteuid(nobody.pw_uid)


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

    def _create_submit_code_file(self, file_name):
        """ Write the code (`answer`) to a file and set the file path"""
        # File name/extension depending on the question language
        submit_f = open(file_name, 'w')
        submit_f.write(self.user_answer.lstrip())
        submit_f.close()
        submit_path = abspath(submit_f.name)
        if sfile_elf.language == "bash":
            self._set_file_as_executable(submit_path)

        return submit_path

    def _set_file_as_executable(self, fname):
        os.chmod(fname,  stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
                 | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
                 | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)

    def _set_test_code_file_path(self, ref_path=None, test_case_path=None):
        # ref_path, test_case_path = self.ref_code_path.split(',')

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
        return proc, stdout, stderr

    def _compile_command(self, cmd, *args, **kw):
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


###############################################################################
# `CodeServer` class.
###############################################################################
class CodeServer(object):
    """A code server that executes user submitted test code, tests it and
    reports if the code was correct or not.
    """
    def __init__(self, port, queue):
        self.port = port
        self.queue = queue

    def check_code(self, info_parameter, in_dir=None):
        """Calls the TestCode Class to test the current code"""
        info_parameter = json.loads(info_parameter)
        test_parameter = info_parameter.get("test_parameter")
        language = info_parameter.get("language")
        user_answer = info_parameter.get("user_answer")
        ref_code_path = info_parameter.get("ref_code_path")

        eval_module_name = "evaluate_{0}".format(language.lower())
        eval_class_name = "Evaluate{0}".format(language.capitalize())

        get_class = self._sub_class_factory(eval_module_name, eval_class_name)

        test_code_class = get_class(test_parameter, language, user_answer, ref_code_path, in_dir)
        result = test_code_class.run_code()
        # Put us back into the server pool queue since we are free now.
        self.queue.put(self.port)

        return json.dumps(result)

    def _sub_class_factory(self, module_name, class_name):
        # load the module, will raise ImportError if module cannot be loaded
        get_module = importlib.import_module(module_name)
        # get the class, will raise AttributeError if class cannot be found
        get_class = getattr(get_module, class_name)

        return get_class

    def run(self):
        """Run XMLRPC server, serving our methods."""
        server = SimpleXMLRPCServer(("localhost", self.port))
        self.server = server
        server.register_instance(self)
        self.queue.put(self.port)
        server.serve_forever()


###############################################################################
# `ServerPool` class.
###############################################################################
class ServerPool(object):
    """Manages a pool of CodeServer objects."""
    def __init__(self, ports, pool_port=50000):
        """Create a pool of servers.  Uses a shared Queue to get available
        servers.

        Parameters
        ----------

        ports : list(int)
            List of ports at which the CodeServer's should run.

        pool_port : int
            Port at which the server pool should serve.
        """
        self.my_port = pool_port
        self.ports = ports
        queue = Queue(maxsize=len(ports))
        self.queue = queue
        servers = []
        for port in ports:
            server = CodeServer(port, queue)
            servers.append(server)
            p = Process(target=server.run)
            p.start()
        self.servers = servers

    def get_server_port(self):
        """Get available server port from ones in the pool.  This will block
        till it gets an available server.
        """
        q = self.queue
        was_waiting = True if q.empty() else False
        port = q.get()
        if was_waiting:
            print '*'*80
            print "No available servers, was waiting but got server \
                   later at %d." % port
            print '*'*80
            sys.stdout.flush()
        return port

    def run(self):
        """Run server which returns an available server port where code
        can be executed.
        """
        server = SimpleXMLRPCServer(("localhost", self.my_port))
        self.server = server
        server.register_instance(self)
        server.serve_forever()


###############################################################################
def main():
    run_as_nobody()
    if len(sys.argv) == 1:
        ports = SERVER_PORTS
    else:
        ports = [int(x) for x in sys.argv[1:]]

    server_pool = ServerPool(ports=ports, pool_port=SERVER_POOL_PORT)
    server_pool.run()

if __name__ == '__main__':
    main()
