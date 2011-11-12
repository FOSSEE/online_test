#!/usr/bin/env python
"""This server runs an XMLRPC server that can be submitted code and tests
and returns the output.  It *should* be run as root and will run as the user 
'nobody' so as to minimize any damange by errant code.
"""
import sys
from SimpleXMLRPCServer import SimpleXMLRPCServer
import pwd
import os


# Set the effective uid
nobody = pwd.getpwnam('nobody')
os.seteuid(nobody.pw_uid)


def run_code(answer, test_code, in_dir=None):
    """Tests given Python function (`answer`) with the `test_code` supplied.  
    If the optional `in_dir` keyword argument is supplied it changes the 
    directory to that directory (it does not change it back to the original when
    done).

    Returns
    -------
    
    A tuple: (success, error message).
    
    """
    if in_dir is not None:
        os.chdir(in_dir)
        
    success = False
    tb = None
    try:
        submitted = compile(answer, '<string>', mode='exec')
        g = {}
        exec submitted in g
        _tests = compile(test_code, '<string>', mode='exec')
        exec _tests in g
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

    return success, err


def main():
    server = SimpleXMLRPCServer(("localhost", 8001))
    server.register_function(run_code)
    server.serve_forever()
    
if __name__ == '__main__':
    main()
    