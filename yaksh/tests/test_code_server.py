from __future__ import unicode_literals
import json
try:
    from Queue import Queue
except ImportError:
    from queue import Queue
from threading import Thread
import unittest
from six.moves import urllib

from yaksh.code_server import ServerPool, SERVER_POOL_PORT
from yaksh import settings
from yaksh.xmlrpc_clients import CodeServerProxy


class TestCodeServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        settings.code_evaluators['python']['standardtestcase'] = \
            "yaksh.python_assertion_evaluator.PythonAssertionEvaluator"
        ports = range(8001, 8006)   
        server_pool = ServerPool(ports=ports, pool_port=SERVER_POOL_PORT)
        cls.server_pool = server_pool
        cls.server_thread = t = Thread(target=server_pool.run)
        t.start()

    @classmethod
    def tearDownClass(cls):
        cls.server_pool.stop()
        cls.server_thread.join()
        settings.code_evaluators['python']['standardtestcase'] = \
            "python_assertion_evaluator.PythonAssertionEvaluator"

    def setUp(self):
        self.code_server = CodeServerProxy()

    def test_inifinite_loop(self):
        # Given
        testdata = {'user_answer': 'while True: pass',
                    'test_case_data': [{'test_case':'assert 1==2'}]}

        # When
        result = self.code_server.run_code(
            'python', 'standardtestcase', json.dumps(testdata), ''
        )

        # Then
        data = json.loads(result)
        self.assertFalse(data['success'])
        self.assertTrue('infinite loop' in data['error'])

    def test_correct_answer(self):
        # Given
        testdata = {'user_answer': 'def f(): return 1',
                    'test_case_data': [{'test_case':'assert f() == 1'}]}

        # When
        result = self.code_server.run_code(
            'python', 'standardtestcase', json.dumps(testdata), ''
        )

        # Then
        data = json.loads(result)
        self.assertTrue(data['success'])
        self.assertEqual(data['error'], 'Correct answer')

    def test_wrong_answer(self):
        # Given
        testdata = {'user_answer': 'def f(): return 1',
                    'test_case_data': [{'test_case':'assert f() == 2'}]}

        # When
        result = self.code_server.run_code(
            'python', 'standardtestcase', json.dumps(testdata), ''
        )

        # Then
        data = json.loads(result)
        self.assertFalse(data['success'])
        self.assertTrue('AssertionError' in data['error'])

    def test_multiple_simultaneous_hits(self):
        # Given
        results = Queue()

        def run_code():
            """Run an infinite loop."""
            testdata = {'user_answer': 'while True: pass',
                        'test_case_data': [{'test_case':'assert 1==2'}]}
            result = self.code_server.run_code(
                'python', 'standardtestcase', json.dumps(testdata), ''
            )
            results.put(json.loads(result))

        N = 10
        # When
        import time
        threads = []
        for i in range(N):
            t = Thread(target=run_code)
            threads.append(t)
            t.start()

        for t in threads:
            if t.isAlive():
                t.join()

        # Then
        self.assertEqual(results.qsize(), N)
        for i in range(N):
            data = results.get()
            self.assertFalse(data['success'])
            self.assertTrue('infinite loop' in data['error'])

    def test_server_pool_status(self):
        # Given
        url = "http://localhost:%s/status"%SERVER_POOL_PORT

        # When
        response = urllib.request.urlopen(url)
        data = response.read().decode('utf-8')

        # Then
        expect = 'out of 5 are free'
        self.assertTrue(expect in data)
        expect = 'Load:'
        self.assertTrue(expect in data)


if __name__ == '__main__':
    unittest.main()
