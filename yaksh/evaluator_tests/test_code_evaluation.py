import unittest
import os
from yaksh import python_assertion_evaluator
from yaksh.language_registry import _LanguageRegistry, get_registry
from yaksh.settings import SERVER_TIMEOUT


class RegistryTestCase(unittest.TestCase):
    def setUp(self):
        self.registry_object = get_registry()
        self.language_registry = _LanguageRegistry()

    def test_set_register(self):
        class_name = getattr(python_assertion_evaluator, 'PythonAssertionEvaluator')
        self.registry_object.register("python", {"standardtestcase": "yaksh.python_assertion_evaluator.PythonAssertionEvaluator",
                    "stdoutbasedtestcase": "python_stdout_evaluator.PythonStdoutEvaluator"
            })
        self.assertEquals(self.registry_object.get_class("python", "standardtestcase"), class_name)

    def tearDown(self):
        self.registry_object = None


if __name__ == '__main__':
    unittest.main()
