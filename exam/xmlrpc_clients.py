from xmlrpclib import ServerProxy
from settings import SERVER_PORTS
import random
import socket


class CodeServer(object):
    """A class that manages accesing the farm of Python servers and making
    calls to them such that no one XMLRPC server is overloaded.
    """
    def __init__(self):
        servers = [ServerProxy('http://localhost:%d'%(x)) for x in SERVER_PORTS]
        self.servers = servers
        self.indices = range(len(SERVER_PORTS))
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
        done = False
        result = [False, 'Unable to connect to any code servers!']
        # Try to connect a few times if not, quit.
        count = 5
        while (not done) and (count > 0):
            try:
                server = self._get_server()
                method = getattr(server, method_name)
                result = method(answer, test_code, user_dir)
            except socket.error:
                count -= 1
            else:
                done = True
        return result

    def _get_server(self):
        # pick a suitable server at random from our pool of servers.
        index = random.choice(self.indices)
        return self.servers[index]

# views.py calls this Python server which forwards the request to one
# of the running servers.
code_server = CodeServer()

