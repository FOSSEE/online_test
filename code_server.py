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
from os.path import isdir, dirname, abspath, join
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
            err = 'Code took more than %s seconds to run.'%SERVER_TIMEOUT
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

        """Tests given Bash code  (`answer`) with the `test_code` supplied.  It
        assumes that there are two parts to the test_code separated by '#++++++'.

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

        # XXX: fix this to not hardcode it to 6 +'s!
        reference, args = test_code.split('#++++++')
        ref_f = open('reference.sh', 'w')
        ref_f.write(reference); ref_f.close()
        ref_fname = abspath(ref_f.name)
        _set_exec(ref_fname)
        args_f = open('reference.args', 'w')
        args_f.write(args); args_f.close()
        _set_exec(args_f.name)
        submit_f = open('submit.sh', 'w')
        submit_f.write(answer); submit_f.close()
        submit_fname = abspath(submit_f.name)
        _set_exec(submit_fname)

        tester = join(MY_DIR, 'shell_script_tester.sh')

        # Run the shell code in a subprocess.
        try:
            output = subprocess.check_output([tester, ref_fname, submit_fname],
                                             stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, exc:
            success = False
            err = 'Error: exist status: %d, message: %s'%(exc.returncode,
                                                         exc.output)
        else:
            success = True
            err = 'Correct answer'

        # Put us back into the server pool queue since we are free now.
        self.queue.put(self.port)
        return success, err

    def run(self):
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
