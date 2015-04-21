#!/usr/bin/env python

class Registry(object):
    def __init__(self):
        self._registry = {}

    def get_class(self, language):
        return self._registry[language]

    def register(self, language, cls):
        self._registry[language] = cls


registry = Registry()