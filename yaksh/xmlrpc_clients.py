from __future__ import unicode_literals
import time
import random
import socket
import json
import urllib
from six.moves import urllib

try:
    from xmlrpclib import ServerProxy
except ImportError:
    # The above import will not work on Python-3.x.
    from xmlrpc.client import ServerProxy

# Local imports
from .settings import SERVER_PORTS, SERVER_POOL_PORT


class ConnectionError(Exception):
    pass

###############################################################################
# `CodeServerProxy` class.
###############################################################################


class CodeServerProxy(object):
    """A class that manages accesing the farm of Python servers and making
    calls to them such that no one XMLRPC server is overloaded.
    """
    def __init__(self):
        pool_url = 'http://localhost:%d' % (SERVER_POOL_PORT)
        self.pool_url = pool_url

    def run_code(self, language, json_data, user_dir):
        """Tests given code (`answer`) with the `test_code` supplied.  If the
        optional `in_dir` keyword argument is supplied it changes the directory
        to that directory (it does not change it back to the original when
        done).  The parameter language specifies which language to use for the
        tests.

        Parameters
        ----------
        json_data contains;
        user_answer : str
            The user's answer for the question.
        test_code : str
            The test code to check the user code with.
        language : str
            The programming language to use.

        user_dir : str (directory)
            The directory to run the tests inside.


        Returns
        -------
        A json string of a dict containing: 
        {"success": success, "weight": weight, "error": error message}

        success - Boolean, indicating if code was executed successfully, correctly
        weight - Float, indicating total weight of all successful test cases
        error - String, error message if success is false
        """

        try:
            server = self._get_server()
            result = server.check_code(language, json_data, user_dir)
        except ConnectionError:
            result = json.dumps({'success': False,
                'weight': 0.0,
                'error': ['Unable to connect to any code servers!']
                })
        return result

    def _get_server(self):
        response = urllib.request.urlopen(self.pool_url)
        port = json.loads(response.read().decode('utf-8'))
        proxy = ServerProxy('http://localhost:%d' % port)
        return proxy

# views.py calls this Python server which forwards the request to one
# of the running servers.
code_server = CodeServerProxy()
