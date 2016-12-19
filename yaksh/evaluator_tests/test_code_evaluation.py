from __future__ import unicode_literals
import unittest
import os
from yaksh import python_assertion_evaluator
from yaksh.language_registry import _LanguageRegistry, get_registry
from yaksh.settings import SERVER_TIMEOUT, code_evaluators


class RegistryTestCase(unittest.TestCase):
    def setUp(self):
        self.registry_object = get_registry()
        self.language_registry = _LanguageRegistry()
        assertion_evaluator_path = ("yaksh.python_assertion_evaluator"
            ".PythonAssertionEvaluator"
        )
        stdio_evaluator_path = ("yaksh.python_stdio_evaluator."
            "PythonStdioEvaluator"
        )
        code_evaluators['python'] = \
        {"standardtestcase": assertion_evaluator_path,
        "stdiobasedtestcase": stdio_evaluator_path
        }

    def test_set_register(self):
        evaluator_class = self.registry_object.get_class("python", 
            "standardtestcase"
        )
        assertion_evaluator_path = ("yaksh.python_assertion_evaluator"
            ".PythonAssertionEvaluator"
        )
        stdio_evaluator_path = ("yaksh.python_stdio_evaluator."
            "PythonStdioEvaluator"
        )
        class_name = getattr(python_assertion_evaluator, 
            'PythonAssertionEvaluator'
        )
        self.registry_object.register("python", 
            {"standardtestcase": assertion_evaluator_path,
                "stdiobasedtestcase": stdio_evaluator_path
            }
        )
        self.assertEqual(evaluator_class, class_name)

    def tearDown(self):
        self.registry_object = None


if __name__ == '__main__':
    unittest.main()
