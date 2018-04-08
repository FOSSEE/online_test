"""
settings for code_server
"""

from decouple import config

# The number of code server processes to run..
N_CODE_SERVERS = config('N_CODE_SERVERS', default=5, cast=int)

# The server pool port.  This is the server which returns available server
# ports so as to minimize load.  This is some random number where no other
# service is running.  It should be > 1024 and less < 65535 though.
SERVER_POOL_PORT = config('SERVER_POOL_PORT', default=55555, cast=int)

SERVER_HOST_NAME = config('SERVER_HOST_NAME', default='http://localhost')
#'localhost'

# Timeout for the code to run in seconds.  This is an integer!
SERVER_TIMEOUT = config('SERVER_TIMEOUT', default=4, cast=int)

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
