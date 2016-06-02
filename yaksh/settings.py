"""
settings for yaksh app.
"""
# The ports the code server should run on.  This will run one separate
# server for each port listed in the following list.
SERVER_PORTS = [8001]  # range(8001, 8026)

# The server pool port.  This is the server which returns available server
# ports so as to minimize load.  This is some random number where no other
# service is running.  It should be > 1024 and less < 65535 though.
SERVER_POOL_PORT = 53579

# Timeout for the code to run in seconds.  This is an integer!
SERVER_TIMEOUT = 4

# The root of the URL, for example you might be in the situation where you
# are not hosted as host.org/exam/  but as host.org/foo/exam/ for whatever
# reason set this to the root you have to serve at.  In the above example
# host.org/foo/exam set URL_ROOT='/foo'
URL_ROOT = ''

code_evaluators = {
    "python": {"standardtestcase": "python_assertion_evaluator.PythonAssertionEvaluator",
        "stdoutbasedtestcase": "python_stdout_evaluator.PythonStdoutEvaluator"
    },
    "c": {"standardtestcase": "cpp_code_evaluator.CppCodeEvaluator",
        "stdiobasedtestcase": "cpp_stdio_evaluator.CppStdioEvaluator"},
    "cpp": {"standardtestcase": "cpp_code_evaluator.CppCodeEvaluator",
        "stdiobasedtestcase": "cpp_stdio_evaluator.CppStdioEvaluator"},
    "java": {"standardtestcase": "java_code_evaluator.JavaCodeEvaluator",
        "stdiobasedtestcase": "java_stdio_evaluator.JavaStdioEvaluator"},
    "bash": {"standardtestcase": "bash_code_evaluator.BashCodeEvaluator"},
    "scilab": {"standardtestcase": "scilab_code_evaluator.ScilabCodeEvaluator"},
}
