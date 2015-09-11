import unittest
import os
from testapp.yaksh import python_code_evaluator
from testapp.yaksh.language_registry import _LanguageRegistry, set_registry, get_registry
from testapp.yaksh.settings import SERVER_TIMEOUT


class RegistryTestCase(unittest.TestCase):
    def setUp(self):
        set_registry()
        self.registry_object = get_registry()
        self.language_registry = _LanguageRegistry()

    def test_set_register(self):
        class_name = getattr(python_code_evaluator, 'PythonCodeEvaluator')
        self.registry_object.register("python", "testapp.yaksh.python_code_evaluator.PythonCodeEvaluator")
        self.assertEquals(self.registry_object.get_class("python"), class_name)

    def tearDown(self):
        self.registry_object = None


if __name__ == '__main__':
    unittest.main()
