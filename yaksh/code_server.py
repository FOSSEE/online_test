#!/usr/bin/env python

"""This server runs an HTTP server (using tornado) and several code servers
using XMLRPC that can be submitted code
and tests and returns the output.  It *should* be run as root and will run as
the user 'nobody' so as to minimize any damange by errant code.  This can be
configured by editing settings.py to run as many servers as desired.  One can
also specify the ports on the command line.  Here are examples::

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

# Standard library imports
from __future__ import unicode_literals
import json
from multiprocessing import Process, Queue
import os
from os.path import isdir, dirname, abspath, join, isfile
import pwd
import re
import signal
import stat
import subprocess
import sys

try:
    from SimpleXMLRPCServer import SimpleXMLRPCServer
except ImportError:
    # The above import will not work on Python-3.x.
    from xmlrpc.server import SimpleXMLRPCServer

try:
    from urllib import unquote
except ImportError:
    # The above import will not work on Python-3.x.
    from urllib.parse import unquote

# Library imports
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler

# Local imports
from .settings import SERVER_PORTS, SERVER_POOL_PORT
from .language_registry import create_evaluator_instance
from .grader import Grader


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
        data = json.loads(json_data)
        grader = Grader(in_dir)
        result = grader.evaluate(data) 

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
        queue = Queue(maxsize=len(self.ports))
        self.queue = queue
        servers = []
        processes = []
        for port in self.ports:
            server = CodeServer(port, queue)
            servers.append(server)
            p = Process(target=server.run)
            processes.append(p)
        self.servers = servers
        self.processes = processes
        self.app = self._make_app()

    def _make_app(self):
        app = Application([
            (r"/.*", MainHandler, dict(server=self)),
        ])
        app.listen(self.my_port)
        return app

    def _start_code_servers(self):
        for proc in self.processes:
            if proc.pid is None:
                proc.start()

    # Public Protocol ##########

    def get_server_port(self):
        """Get available server port from ones in the pool.  This will block
        till it gets an available server.
        """
        return self.queue.get()

    def get_status(self):
        """Returns current queue size and total number of ports used."""
        try:
            qs = self.queue.qsize()
        except NotImplementedError:
            # May not work on OS X so we return a dummy.
            qs = len(self.ports)

        return qs, len(self.ports)

    def run(self):
        """Run server which returns an available server port where code
        can be executed.
        """
        # We start the code servers here to ensure they are run as nobody.
        self._start_code_servers()
        IOLoop.current().start()

    def stop(self):
        """Stop all the code server processes.
        """
        for proc in self.processes:
            proc.terminate()
        IOLoop.current().stop()


class MainHandler(RequestHandler):
    def initialize(self, server):
        self.server = server

    def get(self):
        path = self.request.path[1:]
        if len(path) == 0:
            port = self.server.get_server_port()
            self.write(str(port))
        elif path == "status":
            q_size, total = self.server.get_status()
            result = "%d servers out of %d are free.\n"%(q_size, total)
            load = float(total - q_size)/total*100
            result += "Load: %s%%\n"%load
            self.write(result)


###############################################################################
def main(args=None):
    if args:
        ports = [int(x) for x in args]
    else:
        ports = SERVER_PORTS

    server_pool = ServerPool(ports=ports, pool_port=SERVER_POOL_PORT)
    # This is done *after* the server pool is created because when the tornado
    # app calls listen(), it cannot be nobody.
    run_as_nobody()

    server_pool.run()

if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
