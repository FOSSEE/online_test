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
# Local imports.
from settings import SERVER_PORTS, SERVER_POOL_PORT
from language_registry import set_registry, get_registry


MY_DIR = abspath(dirname(__file__))


# Private Protocol ##########
def run_as_nobody():
    """Runs the current process as nobody."""
    # Set the effective uid and to that of nobody.
    nobody = pwd.getpwnam('nobody')
    os.setegid(nobody.pw_gid)
    os.seteuid(nobody.pw_uid)


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

    # Public Protocol ##########
    def check_code(self, language, json_data, in_dir=None):
        """Calls relevant EvaluateCode class based on language to check the
         answer code
        """
        code_evaluator = self._create_evaluator_instance(language, json_data,
                                                             in_dir)
        result = code_evaluator.evaluate()

        # Put us back into the server pool queue since we are free now.
        self.queue.put(self.port)

        return json.dumps(result)

    def run(self):
        """Run XMLRPC server, serving our methods."""
        server = SimpleXMLRPCServer(("0.0.0.0", self.port))
        self.server = server
        server.register_instance(self)
        self.queue.put(self.port)
        server.serve_forever()

    # Private Protocol ##########
    def _create_evaluator_instance(self, language, json_data, in_dir):
        """Create instance of relevant EvaluateCode class based on language"""
        set_registry()
        registry = get_registry()
        cls = registry.get_class(language)
        instance = cls.from_json(language, json_data, in_dir)
        return instance


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

    # Public Protocol ##########

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
        server = SimpleXMLRPCServer(("0.0.0.0", self.my_port))
        self.server = server
        server.register_instance(self)
        server.serve_forever()


###############################################################################
def main(args=None):
    run_as_nobody()
    if args:
        ports = [int(x) for x in args[1:]]
    else:
        ports = SERVER_PORTS

    server_pool = ServerPool(ports=ports, pool_port=SERVER_POOL_PORT)
    server_pool.run()

if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
