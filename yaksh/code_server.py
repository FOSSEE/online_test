#!/usr/bin/env python

"""This server runs an HTTP server (using tornado) to which code can be
submitted for checking. This is asynchronous so once submitted the user can
check for the result.

It *should* be run as root and will run as the user 'nobody' so as to minimize
any damange by errant code. This can be configured by editing settings.py to
run as many servers as desired.

"""

# Standard library imports
from __future__ import unicode_literals
from argparse import ArgumentParser
import asyncio
import json
from multiprocessing import Process, Queue, Manager
import os
from os.path import dirname, abspath
try:
    import pwd
except ImportError:
    pass
import sys
import threading
import time

# Library imports
import requests
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_sockets
from tornado.web import Application, RequestHandler
import urllib

# Local imports
from .settings import N_CODE_SERVERS, SERVER_POOL_PORT
from .grader import Grader


MY_DIR = abspath(dirname(__file__))


# Private Protocol ##########
def run_as_nobody():
    """Runs the current process as nobody."""
    # Set the effective uid and to that of nobody.
    nobody = pwd.getpwnam('nobody')
    os.setegid(nobody.pw_gid)
    os.seteuid(nobody.pw_uid)


def check_code(pid, job_queue, results):
    """Check the code, this runs forever.
    """
    while True:
        uid, json_data, user_dir = job_queue.get(True)
        results[uid] = dict(status='running', pid=pid, result=None)
        data = json.loads(json_data)
        grader = Grader(user_dir)
        result = grader.evaluate(data)
        results[uid] = dict(status='done', result=json.dumps(result))


###############################################################################
# `ServerPool` class.
###############################################################################
class ServerPool(object):
    """Manages a pool of processes checking code."""
    def __init__(self, n, pool_port=50000):
        """Create a pool of servers.

        Parameters
        ----------

        n : int
            Number of code servers to run

        pool_port : int
            Port at which the server pool should serve.
        """
        self.n = n
        self.manager = Manager()
        self.results = self.manager.dict()
        self.my_port = pool_port

        self.job_queue = Queue()
        processes = []
        for i in range(n):
            p = self._make_process(i)
            processes.append(p)
        self.processes = processes
        self.app = self._make_app()
        # Bind the port now, so an error (port in use) shows up here and
        # requests sent before run() wait in the socket's queue. The sockets
        # are served by the event loop of the thread that calls run().
        self._sockets = bind_sockets(int(self.my_port))
        self._started = threading.Event()
        self._loop = None
        self._stop_event = None

    def _make_app(self):
        return Application([
            (r"/.*", MainHandler, dict(server=self)),
        ])

    def _make_process(self, pid):
        return Process(
            target=check_code, args=(pid, self.job_queue, self.results)
        )

    def _start_code_servers(self):
        for proc in self.processes:
            if proc.pid is None:
                proc.start()

    def _handle_dead_process(self, result):
        if result.get('status') == 'running':
            pid = result.get('pid')
            proc = self.processes[pid]
            if not proc.is_alive():
                # If the processes is dead, something bad happened so
                # restart that process.
                new_proc = self._make_process(pid)
                self.processes[pid] = new_proc
                new_proc.start()
                result['status'] = 'done'
                result['result'] = json.dumps(dict(
                    success=False, weight=0.0,
                    error=['Process ended with exit code %s.'
                           % proc.exitcode]
                ))

    # Public Protocol ##########

    def get_status(self):
        """Returns current job queue size, total number of processes alive.
        """
        qs = sum(r['status'] == 'not started'
                 for r in self.results.values())
        alive = sum(p.is_alive() for p in self.processes)
        n_running = sum(r['status'] == 'running'
                        for r in self.results.values())

        return qs, alive, n_running

    def submit(self, uid, json_data, user_dir):
        self.results[uid] = dict(status='not started')
        self.job_queue.put((uid, json_data, user_dir))

    def get_result(self, uid):
        result = self.results.get(uid, dict(status='unknown'))
        self._handle_dead_process(result)
        if result.get('status') == 'done':
            self.results.pop(uid)
        return json.dumps(result)

    def run(self):
        """Run server which returns an available server port where code
        can be executed.
        """
        # We start the code servers here to ensure they are run as nobody.
        self._start_code_servers()
        # Tornado 5+ runs on asyncio, which has one event loop per thread;
        # tests call run() in a new thread. asyncio.run() gives this thread
        # its own loop, as Tornado's documentation recommends.
        asyncio.run(self._serve())

    async def _serve(self):
        self._loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()
        http_server = HTTPServer(self.app)
        http_server.add_sockets(self._sockets)
        self._started.set()
        try:
            await self._stop_event.wait()
        finally:
            http_server.stop()
            await http_server.close_all_connections()

    def stop(self):
        """Stop all the code server processes.
        """
        for proc in self.processes:
            proc.terminate()
        if self._started.wait(timeout=10):
            # stop() is usually called from another thread: ask the loop's
            # own thread to finish _serve().
            self._loop.call_soon_threadsafe(self._stop_event.set)
        else:
            for sock in self._sockets:
                sock.close()


class MainHandler(RequestHandler):
    def initialize(self, server):
        self.server = server

    def get(self):
        path = self.request.path[1:]
        if len(path) == 0:
            q_size, alive, running = self.server.get_status()
            result = "%d processes, %d running, %d queued" % (
                alive, running, q_size
            )
            self.write(result)
        else:
            uid = path
            json_result = self.server.get_result(uid)
            self.write(json_result)

    def post(self):
        uid = self.get_argument('uid')
        json_data = self.get_argument('json_data')
        user_dir = self.get_argument('user_dir')
        self.server.submit(uid, json_data, user_dir)
        self.write('OK')


def submit(url, uid, json_data, user_dir):
    '''Submit a job to the code server.

    Parameters
    ----------

    url : str
        URL of the server pool.

    uid : str
        Unique ID of the submission.

    json_data : jsonized str
        Data to send to the code checker.

    user_dir : str
        User directory.
    '''
    requests.post(
        url, data=dict(uid=uid, json_data=json_data, user_dir=user_dir)
    )


def get_result(url, uid, block=False):
    '''Get the status of a job submitted to the code server.

    Returns the result currently known in the form of a dict. The dictionary
    contains two keys, 'status' and 'result'. The status can be one of
    ['running', 'not started', 'done', 'unknown']. The result is the result of
    the code execution as a jsonized string.

    Parameters
    ----------

    url : str
        URL of the server pool.

    uid : str
        Unique ID of the submission.

    block : bool
        Set to True if you wish to block till result is done.

    '''
    def _get_data():
        r = requests.get(urllib.parse.urljoin(url, str(uid)))
        return json.loads(r.content.decode('utf-8'))
    data = _get_data()
    if block:
        while data.get('status') != 'done':
            time.sleep(0.1)
            data = _get_data()

    return data


###############################################################################
def main(args=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        'n', nargs='?', type=int, default=N_CODE_SERVERS,
        help="Number of servers to run."
    )
    parser.add_argument(
        '-p', '--port', dest='port', default=SERVER_POOL_PORT,
        help="Port at which the http server should run."
    )

    options = parser.parse_args(args)

    # Called before serverpool is created so that the multiprocessing
    # can work properly.
    run_as_nobody()
    server_pool = ServerPool(n=options.n, pool_port=options.port)

    server_pool.run()


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
