import sys
from .utils import import_by_path
from contextlib import contextmanager


@contextmanager
def redirect_stdout():
    from StringIO import StringIO
    new_target = StringIO()

    old_target, sys.stdout = sys.stdout, new_target # replace sys.stdout
    try:
        yield new_target # run some code with the replaced stdout
    finally:
        sys.stdout = old_target # restore to the previous value

# def redirect_stdout():
#     # import sys
#     from StringIO import StringIO
#     oldout,olderr = sys.stdout, sys.stderr
#     try:
#         out = StringIO()
#         err = StringIO()
#         # sys.stdout,sys.stderr = out, err
#         yield out, err
#     finally:
#         sys.stdout,sys.stderr = oldout, olderr
#         out = out.getvalue()
#         err = err.getvalue()

TESTER_BACKEND = {
    "python": "PythonPrintTesterBackend" #@@@rename to test-case-creator, this file should be backend.py
}

class TesterException(Exception):
    """ Parental class for all tester exceptions """
    pass

class UnknownBackendException(TesterException):
    """ Exception thrown if tester backend is not recognized. """
    pass


def detect_backend(language):
    """
    Detect the right backend for a test case.
    """
    backend_name = TESTER_BACKEND.get(language)
    # backend = import_by_path(backend_name)
    backend = PythonTesterBackend() #@@@
    return backend

class PythonPrintTesterBackend(object):
    def test_code(self, submitted, reference_output):
        """
        create a test command
        """
        with redirect_stdout() as output_buffer: 
            g = {}
            exec submitted in g

        # return_buffer = out.encode('string_escape')
        raw_output_value = output_buffer.getvalue()
        output_value = raw_output_value.encode('string_escape').strip()
        if output_value == str(reference_output):
            return True
        else:
            raise ValueError("Incorrect Answer", output_value, reference_output)


class PythonTesterBackend(object):
    # def __init__(self, test_case):
    #     self._test_case = test_case
    def create(self): #@@@ test()
        """
        create a test command
        """
        test_code = "assert {0}({1}) == {2}".format(self.test_case_parameters['function_name'], self.test_case_parameters['args'],
                                     self.test_case_parameters['expected_answer'])
        return test_code

    def pack(self, test_case):
        kw_args_dict = {}
        pos_args_list = []
        test_case_data = {}
        test_case_data['test_id'] = test_case.id
        test_case_data['func_name'] = test_case.func_name
        test_case_data['expected_answer'] = test_case.expected_answer

        if test_case.kw_args:
            for args in test_case.kw_args.split(","):
                arg_name, arg_value = args.split("=")
                kw_args_dict[arg_name.strip()] = arg_value.strip()

        if test_case.pos_args:
            for args in test_case.pos_args.split(","):
                pos_args_list.append(args.strip())

        test_case_data['kw_args'] = kw_args_dict
        test_case_data['pos_args'] = pos_args_list

        return test_case_data

    def unpack(self, test_case_data):
        pos_args = ", ".join(str(i) for i in test_case_data.get('pos_args')) \
                            if test_case_data.get('pos_args') else ""
        kw_args = ", ".join(str(k+"="+a) for k, a
                         in test_case_data.get('kw_args').iteritems()) \
                        if test_case_data.get('kw_args') else ""
        args = pos_args + ", " + kw_args if pos_args and kw_args \
                                            else pos_args or kw_args
        function_name = test_case_data.get('func_name')
        expected_answer = test_case_data.get('expected_answer')

        self.test_case_parameters = {
            'args': args,
            'function_name': function_name,
            'expected_answer': expected_answer
        }

        return self.test_case_parameters