#!/usr/bin/env python
"""This server runs an XMLRPC server that can be submitted code and tests
and returns the output.  It *should* be run as root and will run as the user 
'nobody' so as to minimize any damange by errant code.
"""
import sys
import traceback
from SimpleXMLRPCServer import SimpleXMLRPCServer
import pwd
import os
from os.path import isdir
import signal
from settings import SERVER_PORT, SERVER_TIMEOUT


def run_as_nobody():
    # Set the effective uid
    nobody = pwd.getpwnam('nobody')
    os.setegid(nobody.pw_gid)
    os.seteuid(nobody.pw_uid)

# Raised when the code times-out.
# c.f. http://pguides.net/python/timeout-a-function
class TimeoutException(Exception):
    pass
    
def timeout_handler(signum, frame):
    raise TimeoutException('Code took too long to run.')


def run_code(answer, test_code, in_dir=None):
    """Tests given Python function (`answer`) with the `test_code` supplied.  
    If the optional `in_dir` keyword argument is supplied it changes the 
    directory to that directory (it does not change it back to the original when
    done).  This function also timesout when the function takes more than 
    SERVER_TIMEOUT seconds to run to prevent runaway code.

    Returns
    -------
    
    A tuple: (success, error message).
    
    """
    if in_dir is not None and isdir(in_dir):
        os.chdir(in_dir)
        
    # Add a new signal handler for the execution of this code.
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(SERVER_TIMEOUT)
     
    success = False
    tb = None
    try:
        submitted = compile(answer, '<string>', mode='exec')
        g = {}
        exec submitted in g
        _tests = compile(test_code, '<string>', mode='exec')
        exec _tests in g
    except TimeoutException:
        err = 'Code took more than %s seconds to run.'%SERVER_TIMEOUT
    except AssertionError:
        type, value, tb = sys.exc_info()
        info = traceback.extract_tb(tb)
        fname, lineno, func, text = info[-1]
        text = str(test_code).splitlines()[lineno-1]
        err = "{0} {1} in: {2}".format(type.__name__, str(value), text)
    except:
        type, value = sys.exc_info()[:2]
        err = "Error: {0}".format(repr(value))
    else:
        success = True
        err = 'Correct answer'
    finally:
        del tb
        # Set back any original signal handler.
        signal.signal(signal.SIGALRM, old_handler) 
        
    # Cancel the signal if any, see signal.alarm documentation.
    signal.alarm(0)

    return success, err


def main():
    run_as_nobody()
    server = SimpleXMLRPCServer(("localhost", SERVER_PORT))
    server.register_function(run_code)
    server.serve_forever()
    
if __name__ == '__main__':
    main()
    