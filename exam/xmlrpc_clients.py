from xmlrpclib import ServerProxy
from settings import SERVER_PORTS
import random
import socket


class PythonServer(object):
    """A class that manages accesing the farm of Python servers and making
    calls to them such that no one XMLRPC server is overloaded.
    """
    def __init__(self):
        servers = [ServerProxy('http://localhost:%d'%(x)) for x in SERVER_PORTS]
        self.servers = servers
        self.indices = range(len(SERVER_PORTS))
    
    def run_code(self, answer, test_code, user_dir):
        """See the documentation of the method of the same name in 
        python_server.py.
        """
        done = False
        result = [False, 'Unable to connect to any Python servers!']
        # Try to connect a few times if not, quit.
        count = 5
        while (not done) and (count > 0):
            try:
                server = self._get_server()
                result = server.run_code(answer, test_code, user_dir)
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
python_server = PythonServer()
