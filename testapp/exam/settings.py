"""
settings for exam app.
"""
# The ports the code server should run on.  This will run one separate
# server for each port listed in the following list.
SERVER_PORTS = [8001]  # range(8001, 8026)

# The server pool port.  This is the server which returns available server
# ports so as to minimize load.  This is some random number where no other
# service is running.  It should be > 1024 and less < 65535 though.
SERVER_POOL_PORT = 53579

# Timeout for the code to run in seconds.  This is an integer!
SERVER_TIMEOUT = 2

# The root of the URL, for example you might be in the situation where you
# are not hosted as host.org/exam/  but as host.org/foo/exam/ for whatever
# reason set this to the root you have to serve at.  In the above example
# host.org/foo/exam set URL_ROOT='/foo'
URL_ROOT = ''

language_register = {"python": "python_code_evaluator",
					 "c": "c_cpp_code_evaluator",
					 "cpp": "c_cpp_code_evaluator",
					 "java": "java_evaluator",
					 "bash": "bash_evaluator",
					 "scilab": "scilab_evaluator",
					}
