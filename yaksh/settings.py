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
    "python": {"standardtestcase": "yaksh.python_assertion_evaluator.PythonAssertionEvaluator",
               "stdiobasedtestcase": "yaksh.python_stdio_evaluator.PythonStdIOEvaluator",
               "hooktestcase": "yaksh.hook_evaluator.HookEvaluator"
               },
    "c": {"standardtestcase": "yaksh.cpp_code_evaluator.CppCodeEvaluator",
          "stdiobasedtestcase": "yaksh.cpp_stdio_evaluator.CppStdIOEvaluator",
          "hooktestcase": "yaksh.hook_evaluator.HookEvaluator"
          },
    "cpp": {"standardtestcase": "yaksh.cpp_code_evaluator.CppCodeEvaluator",
            "stdiobasedtestcase": "yaksh.cpp_stdio_evaluator.CppStdIOEvaluator",
            "hooktestcase": "yaksh.hook_evaluator.HookEvaluator"
            },
    "java": {"standardtestcase": "yaksh.java_code_evaluator.JavaCodeEvaluator",
             "stdiobasedtestcase": "yaksh.java_stdio_evaluator.JavaStdIOEvaluator",
             "hooktestcase": "yaksh.hook_evaluator.HookEvaluator"
             },
    "bash": {"standardtestcase": "yaksh.bash_code_evaluator.BashCodeEvaluator",
             "stdiobasedtestcase": "yaksh.bash_stdio_evaluator.BashStdIOEvaluator",
             "hooktestcase": "yaksh.hook_evaluator.HookEvaluator"
             },
    "scilab": {"standardtestcase": "yaksh.scilab_code_evaluator.ScilabCodeEvaluator",
               "hooktestcase": "yaksh.hook_evaluator.HookEvaluator"
               },
}
