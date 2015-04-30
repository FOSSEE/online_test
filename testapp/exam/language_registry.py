from settings import language_register

registry = None

def set_registry():
    globals registry = _LanguageRegistry()
    
def get_registry():
    return registry

class _LanguageRegistry(object):
    def __init__(self):
        for language, module in language_register.iteritems():
            self._register[language] = None

    # Public Protocol ##########
    def get_class(self, language):
        if not self._register[language]:
            self._register[language] = language_register[language]

        cls = self._register[language]
        module_name, class_name = cls.split(".")
        # load the module, will raise ImportError if module cannot be loaded
        get_module = importlib.import_module(module_name)
        # get the class, will raise AttributeError if class cannot be found
        get_class = getattr(get_module, class_name)
        return get_class

    # def register(self, language, cls):
    #     self._register[language] = cls

