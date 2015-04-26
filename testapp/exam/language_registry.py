#!/usr/bin/env python


class LanguageRegistry(object):
    def __init__(self):
        self._registry = {}

    # Public Protocol ##########
    def get_class(self, language):
        return self._registry[language]

    # Public Protocol ##########
    def register(self, language, cls):
        self._registry[language] = cls


registry = LanguageRegistry()
