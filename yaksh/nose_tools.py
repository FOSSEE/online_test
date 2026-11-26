"""Drop-in replacement for ``nose.tools``.

nose is no longer maintained and does not import on Python 3.12+ (it uses
the removed ``imp`` module). Yaksh puts ``from nose.tools import *`` into
the scope of every Python assertion test case, so existing questions use
``assert_equal``, ``assert_true``, ``ok_``, ``eq_`` and so on.

This module provides the same names, built the same way nose built them:
each ``unittest.TestCase.assertXxx`` method under its pep8 name
``assert_xxx``. The assertion messages are therefore identical.

Aliases that unittest removed in Python 3.12 (``assertEquals``,
``assertRegexpMatches``, ...) are added explicitly, so test cases written
with ``assert_equals`` etc. keep working on new Python versions.

nose's test-runner decorators (``raises``, ``timed``, ``with_setup``,
``istest``, ``nottest``, ...) are not included: they only mean something
to the nose test runner, not inside a Yaksh test case.
"""
import re
import sys
import types
import unittest

__all__ = ['ok_', 'eq_']


class _Dummy(unittest.TestCase):
    def nop(self):
        pass


_t = _Dummy('nop')

_caps = re.compile('([A-Z])')


def _pep8(name):
    return _caps.sub(lambda m: '_' + m.groups()[0].lower(), name)


# Same selection as nose.tools.trivial: assertXxx methods without '_'.
for _name in dir(_t):
    if _name.startswith('assert') and '_' not in _name:
        _pep8_name = _pep8(_name)
        globals()[_pep8_name] = getattr(_t, _name)
        __all__.append(_pep8_name)


# Deprecated unittest aliases removed in Python 3.12. nose exported them on
# older Pythons; keep the names so existing test cases still work.
_REMOVED_ALIASES = {
    'assert_equals': 'assertEqual',
    'assert_not_equals': 'assertNotEqual',
    'assert_almost_equals': 'assertAlmostEqual',
    'assert_not_almost_equals': 'assertNotAlmostEqual',
    'assert_regexp_matches': 'assertRegex',
    'assert_not_regexp_matches': 'assertNotRegex',
    'assert_raises_regexp': 'assertRaisesRegex',
}
for _alias, _target in _REMOVED_ALIASES.items():
    if _alias not in globals():
        globals()[_alias] = getattr(_t, _target)
        __all__.append(_alias)


def _assert_dict_contains_subset(subset, dictionary, msg=None):
    """Same check and message as unittest's assertDictContainsSubset,
    which was removed in Python 3.12."""
    missing = []
    mismatched = []
    for key, value in subset.items():
        if key not in dictionary:
            missing.append(key)
        elif value != dictionary[key]:
            mismatched.append('%s, expected: %s, actual: %s' % (
                unittest.util.safe_repr(key),
                unittest.util.safe_repr(value),
                unittest.util.safe_repr(dictionary[key])))
    if not (missing or mismatched):
        return
    standard_msg = ''
    if missing:
        standard_msg = 'Missing: %s' % ','.join(
            unittest.util.safe_repr(m) for m in missing)
    if mismatched:
        if standard_msg:
            standard_msg += '; '
        standard_msg += 'Mismatched values: %s' % ','.join(mismatched)
    raise AssertionError(_t._formatMessage(msg, standard_msg))


if 'assert_dict_contains_subset' not in globals():
    assert_dict_contains_subset = _assert_dict_contains_subset
    __all__.append('assert_dict_contains_subset')


def ok_(expr, msg=None):
    """Shorthand for assert. Same as nose.tools.ok_."""
    if not expr:
        raise AssertionError(msg)


def eq_(a, b, msg=None):
    """Shorthand for 'assert a == b, "%r != %r" % (a, b)'.
    Same as nose.tools.eq_."""
    if not a == b:
        raise AssertionError(msg or "%r != %r" % (a, b))


def install_as_nose():
    """Make ``import nose.tools`` / ``from nose.tools import ...`` work
    when nose itself is not installed or cannot be imported (Python 3.12+),
    so test cases that import nose explicitly keep working."""
    try:
        import nose.tools  # noqa: F401
        return
    except Exception:
        # ImportError on Python 3.12+ (nose imports the removed 'imp').
        pass
    tools_module = types.ModuleType('nose.tools')
    tools_module.__all__ = list(__all__)
    for name in __all__:
        setattr(tools_module, name, globals()[name])
    nose_module = types.ModuleType('nose')
    nose_module.tools = tools_module
    sys.modules['nose'] = nose_module
    sys.modules['nose.tools'] = tools_module
