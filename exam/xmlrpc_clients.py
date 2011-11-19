from xmlrpclib import ServerProxy
from ..settings import SERVER_PORT

# Connect to the python server.
python_server = ServerProxy('http://localhost:%d'%(SERVER_PORT))
