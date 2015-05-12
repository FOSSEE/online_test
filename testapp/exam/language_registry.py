from settings import code_evaluators
import importlib

registry = None

def set_registry():
    global registry
    registry = _LanguageRegistry()
    
def get_registry():
    return registry

class _LanguageRegistry(object):
    def __init__(self):
        self._register = {}
        for language, module in code_evaluators.iteritems():
            self._register[language] = None

    # Public Protocol ##########
    def get_class(self, language):
        """ Get the code evaluator class for the given language """
        if not self._register.get(language):
            self._register[language] = code_evaluators.get(language)

        cls = self._register[language]
        module_name, class_name = cls.rsplit(".", 1)
        # load the module, will raise ImportError if module cannot be loaded
        get_module = importlib.import_module(module_name)
        # get the class, will raise AttributeError if class cannot be found
        get_class = getattr(get_module, class_name)
        return get_class

    def register(self, language, class_name):
        """ Register a new code evaluator class for language"""
        self._register[language] = class_name

