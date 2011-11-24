from xmlrpclib import ServerProxy
import time
import random
import socket

from settings import SERVER_PORTS, SERVER_POOL_PORT


class ConnectionError(Exception):
    pass

################################################################################
# `CodeServerProxy` class.
################################################################################
class CodeServerProxy(object):
    """A class that manages accesing the farm of Python servers and making
    calls to them such that no one XMLRPC server is overloaded.
    """
    def __init__(self):
        pool_url = 'http://localhost:%d'%(SERVER_POOL_PORT)
        self.pool_server = ServerProxy(pool_url)
        self.methods = {"python": 'run_python_code',
                        "bash": 'run_bash_code'}
    
    def run_code(self, answer, test_code, user_dir, language):
        """Tests given code (`answer`) with the `test_code` supplied.  If the
        optional `in_dir` keyword argument is supplied it changes the directory
        to that directory (it does not change it back to the original when
        done).  The parameter language specifies which language to use for the
        tests.

        Parameters
        ----------
        answer : str
            The user's answer for the question.
        test_code : str
            The test code to check the user code with.
        user_dir : str (directory)
            The directory to run the tests inside.
        language : str
            The programming language to use.

        Returns
        -------
        A tuple: (success, error message).
        """
        method_name = self.methods[language]
        try:
            server = self._get_server()
            method = getattr(server, method_name)
            result = method(answer, test_code, user_dir)
        except ConnectionError:
            result = [False, 'Unable to connect to any code servers!']
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
        proxy = ServerProxy('http://localhost:%d'%port)
        return proxy

# views.py calls this Python server which forwards the request to one
# of the running servers.
code_server = CodeServerProxy()

