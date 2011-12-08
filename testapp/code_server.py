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

# Local imports.
from settings import SERVER_PORTS, SERVER_TIMEOUT, SERVER_POOL_PORT

MY_DIR = abspath(dirname(__file__))

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


################################################################################
# `CodeServer` class.
################################################################################
class CodeServer(object):
    """A code server that executes user submitted test code, tests it and
    reports if the code was correct or not.
    """
    def __init__(self, port, queue):
        self.port = port
        self.queue = queue
        msg = 'Code took more than %s seconds to run. You probably '\
              'have an infinite loop in your code.'%SERVER_TIMEOUT
        self.timeout_msg = msg

    def run_python_code(self, answer, test_code, in_dir=None):
        """Tests given Python function (`answer`) with the `test_code` supplied.  
        If the optional `in_dir` keyword argument is supplied it changes the 
        directory to that directory (it does not change it back to the original when
        done).  This function also timesout when the function takes more than 
        SERVER_TIMEOUT seconds to run to prevent runaway code.

        Returns
        -------
        
        A tuple: (success, error message).
        
        """
        if in_dir is not None and isdir(in_dir):
            os.chdir(in_dir)
            
        # Add a new signal handler for the execution of this code.
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(SERVER_TIMEOUT)
         
        success = False
        tb = None
        try:
            submitted = compile(answer, '<string>', mode='exec')
            g = {}
            exec submitted in g
            _tests = compile(test_code, '<string>', mode='exec')
            exec _tests in g
        except TimeoutException:
            err = self.timeout_msg
        except AssertionError:
            type, value, tb = sys.exc_info()
            info = traceback.extract_tb(tb)
            fname, lineno, func, text = info[-1]
            text = str(test_code).splitlines()[lineno-1]
            err = "{0} {1} in: {2}".format(type.__name__, str(value), text)
        except:
            type, value = sys.exc_info()[:2]
            err = "Error: {0}".format(repr(value))
        else:
            success = True
            err = 'Correct answer'
        finally:
            del tb
            # Set back any original signal handler.
            signal.signal(signal.SIGALRM, old_handler) 
            
        # Cancel the signal if any, see signal.alarm documentation.
        signal.alarm(0)

        # Put us back into the server pool queue since we are free now.
        self.queue.put(self.port)

        return success, err

    def run_bash_code(self, answer, test_code, in_dir=None):
        """Tests given Bash code  (`answer`) with the `test_code` supplied.

        The testcode should typically contain two lines, the first is a path to
        the reference script we are to compare against.  The second is a path
        to the arguments to be supplied to the reference and submitted script.
        The output of these will be compared for correctness.

        If the path's start with a "/" then we assume they are absolute paths.
        If not, we assume they are relative paths w.r.t. the location of this
        code_server script.

        If the optional `in_dir` keyword argument is supplied it changes the 
        directory to that directory (it does not change it back to the original when
        done).

        Returns
        -------
        
        A tuple: (success, error message).
        
        """
        if in_dir is not None and isdir(in_dir):
            os.chdir(in_dir)

        def _set_exec(fname):
            os.chmod(fname,  stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR
                             |stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP
                             |stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH)
        submit_f = open('submit.sh', 'w')
        submit_f.write(answer.lstrip()); submit_f.close()
        submit_path = abspath(submit_f.name)
        _set_exec(submit_path)

        ref_path, test_case_path = test_code.strip().splitlines()
        if not ref_path.startswith('/'):
            ref_path = join(MY_DIR, ref_path)
        if not test_case_path.startswith('/'):
            test_case_path = join(MY_DIR, test_case_path)

        # Add a new signal handler for the execution of this code.
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(SERVER_TIMEOUT)

        # Do whatever testing needed.
        success = False
        try:
            success, err = self.check_bash_script(ref_path, submit_path, test_case_path)
        except TimeoutException:
            err = self.timeout_msg
        except:
            type, value = sys.exc_info()[:2]
            err = "Error: {0}".format(repr(value))
        finally:
            # Set back any original signal handler.
            signal.signal(signal.SIGALRM, old_handler) 

        # Delete the created file.
        os.remove(submit_path)

        # Cancel the signal if any, see signal.alarm documentation.
        signal.alarm(0)

        # Put us back into the server pool queue since we are free now.
        self.queue.put(self.port)

        return success, err

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

    def check_bash_script(self, ref_script_path, submit_script_path, 
                          test_case_path=None):
        """ Function validates student script using instructor script as
        reference. Test cases can optionally be provided.  The first argument
        ref_script_path, is the path to instructor script, it is assumed to
        have executable permission.  The second argument submit_script_path, is
        the path to the student script, it is assumed to have executable
        permission.  The Third optional argument is the path to test the
        scripts.  Each line in this file is a test case and each test case is
        passed to the script as standard arguments.
        
        Returns
        --------

        returns (True, "Correct answer") : If the student script passes all test
        cases/have same output, when compared to the instructor script
        
        returns (False, error_msg): If
        the student script fails a single test/have dissimilar output, when
        compared to the instructor script.
        
        Returns (False, error_msg): If mandatory arguments are not files or if the
        required permissions are not given to the file(s).
        
        """
        if not isfile(ref_script_path):
            return False, "No file at %s"%ref_script_path
        if not isfile(submit_script_path):
            return False, 'No file at %s'%submit_script_path
        if not os.access(ref_script_path, os.X_OK):
            return False, 'Script %s is not executable'%ref_script_path
        if not os.access(submit_script_path, os.X_OK):
            return False, 'Script %s is not executable'%submit_script_path
        
        if test_case_path is None:
            ret = self._run_command(ref_script_path, stdin=None,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc, inst_stdout, inst_stderr = ret
            ret  = self._run_command(submit_script_path, stdin=None,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc, stdnt_stdout, stdnt_stderr = ret
            if inst_stdout == stdnt_stdout:
                return True, 'Correct answer'
            else:
                err = "Error: expected %s, got %s"%(inst_stderr, stdnt_stderr)
                return False, err
        else:
            if not isfile(test_case_path):
                return False, "No test case at %s"%test_case_path
            if not os.access(ref_script_path, os.R_OK):
                return False, "Test script %s, not readable"%test_case_path
            valid_answer = True  # We initially make it one, so that we can stop 
                              # once a test case fails
            loop_count = 0    # Loop count has to be greater than or equal to one.
                              # Useful for caching things like empty test files,etc.
            test_cases = open(test_case_path).readlines()
            num_lines = len(test_cases)
            for test_case in test_cases:
                loop_count += 1
                if valid_answer:
                    args = [ ref_script_path ] + [x for x in test_case.split()]
                    ret = self._run_command(args, stdin=None, 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    proc, inst_stdout, inst_stderr = ret
                    args = [ submit_script_path ] + [x for x in test_case.split()]
                    ret = self._run_command(args, stdin=None, 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    proc, stdnt_stdout, stdnt_stderr = ret
                    valid_answer = inst_stdout == stdnt_stdout
            if valid_answer and (num_lines == loop_count):
                return True, "Correct answer"
            else:
                err = "Error: expected %s, got %s"%(inst_stdout+inst_stderr,
                                                    stdnt_stdout+stdnt_stderr)
                return False, err


    def run(self):
        """Run XMLRPC server, serving our methods.
        """
        server = SimpleXMLRPCServer(("localhost", self.port))
        self.server = server
        server.register_instance(self)
        self.queue.put(self.port)
        server.serve_forever()


################################################################################
# `ServerPool` class.
################################################################################
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
            print "No available servers, was waiting but got server later at %d."%port
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


################################################################################
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
