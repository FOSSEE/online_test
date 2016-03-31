from xmlrpclib import ServerProxy
import time
import random
import socket
import json

from settings import SERVER_PORTS, SERVER_POOL_PORT


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
        self.pool_server = ServerProxy(pool_url)

    def run_code(self, language, test_case_type, json_data, user_dir):
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
        A json string of a dict: {success: success, err: error message}.
        """

        try:
            server = self._get_server()
            result = server.check_code(language, test_case_type, json_data, user_dir)
        except ConnectionError:
            result = json.dumps({'success': False, 'error': 'Unable to connect to any code servers!'})
        return result

    def _get_server(self):
        # Get a suitable server from our pool of servers.  This may block.  We
        # try about 60 times, essentially waiting at most for about 30 seconds.
        done, count = False, 60

        while not done and count > 0:
            try:
                port = self.pool_server.get_server_port()
            except socket.error:
                # Wait a while try again.
                time.sleep(random.random())
                count -= 1
            else:
                done = True
        if not done:
            raise ConnectionError("Couldn't connect to a server!")
        proxy = ServerProxy('http://localhost:%d' % port)
        return proxy

# views.py calls this Python server which forwards the request to one
# of the running servers.
code_server = CodeServerProxy()
