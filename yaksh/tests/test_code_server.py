import json
from multiprocessing import Process
try:
    from Queue import Queue
except ImportError:
    from queue import Queue
from threading import Thread
import unittest


from yaksh.code_server import ServerPool, SERVER_POOL_PORT

from yaksh import settings
from yaksh.xmlrpc_clients import code_server


class TestCodeServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        settings.code_evaluators['python']['standardtestcase'] = \
            "yaksh.python_assertion_evaluator.PythonAssertionEvaluator"
        ports = range(8001, 8006)
        server_pool = ServerPool(ports=ports, pool_port=SERVER_POOL_PORT)
        cls.server_pool = server_pool
        cls.server_proc = p = Process(target=server_pool.run)
        p.start()


    @classmethod
    def tearDownClass(cls):
        cls.server_pool.stop()
        cls.server_proc.terminate()
        settings.code_evaluators['python']['standardtestcase'] = \
            "python_assertion_evaluator.PythonAssertionEvaluator"

    def test_inifinite_loop(self):
        # Given
        testdata = {'user_answer': 'while True: pass',
                    'test_case_data': [{'test_case':'assert 1==2'}]}

        # When
        result = code_server.run_code(
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
        result = code_server.run_code(
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
        result = code_server.run_code(
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
            result = code_server.run_code(
                'python', 'standardtestcase', json.dumps(testdata), ''
            )
            results.put(json.loads(result))

        N = 5
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


if __name__ == '__main__':
    unittest.main()
