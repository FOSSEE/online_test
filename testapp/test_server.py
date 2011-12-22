"""Simple test suite for the code server.  Running this requires that one start
up the code server as::

    $ sudo ./code_server.py

"""
from exam.xmlrpc_clients import code_server

def check_result(result, check='correct answer'):
    if check != 'correct answer':
        assert result[0] == False
    else:
        assert result[0] == True
    if "unable to connect" in result[1].lower():
        assert result[0], result[1]
    assert check in result[1].lower(), result[1]

def test_python():
    """Test if server runs Python code as expected."""
    src = 'while True: pass'
    result = code_server.run_code(src, '', '/tmp', language="python")
    check_result(result, 'more than ')

    src = 'x = 1'
    result = code_server.run_code(src, 'assert x == 1', '/tmp', 
                language="python")
    check_result(result, 'correct answer')

    result = code_server.run_code(src, 'assert x == 0', '/tmp', 
                language="python")
    check_result(result, 'assertionerror')

    src = 'abracadabra'
    result = code_server.run_code(src, 'assert x == 0', '/tmp', 
            language="python")
    check_result(result, 'nameerror')

def test_bash():
    """Test if server runs Bash code as expected."""
    src = """
#!/bin/bash
    [[ $# -eq 2 ]] && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))
    """
    result = code_server.run_code(src, 
            'docs/sample.sh\ndocs/sample.args', '/tmp', language="bash")
    check_result(result)

    src = """
#!/bin/bash
    [[ $# -eq 2 ]] && echo $(( $1 - $2 )) && exit $(( $1 - $2 ))
    """
    result = code_server.run_code(src, 
            'docs/sample.sh\ndocs/sample.args', '/tmp', language="bash")
    check_result(result, 'error')

    src = """\
#!/bin/bash
    while [ 1 ] ; do echo "" > /dev/null ; done
    """
    result = code_server.run_code(src, 
            'docs/sample.sh\ndocs/sample.args', '/tmp', language="bash")
    check_result(result, 'more than ')

    src = '''
#!/bin/bash
    while [ 1 ] ; do echo "" > /dev/null
    '''
    result = code_server.run_code(src, 
            'docs/sample.sh\ndocs/sample.args', '/tmp', language="bash")
    check_result(result, 'error')

    src = '''# Enter your code here.
#!/bin/bash
    while [ 1 ] ; do echo "" > /dev/null
    '''
    result = code_server.run_code(src, 
            'docs/sample.sh\ndocs/sample.args', '/tmp', language="bash")
    check_result(result, 'oserror')

if __name__ == '__main__':
    test_python()
    test_bash()

