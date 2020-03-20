from __future__ import unicode_literals
import json
try:
    from Queue import Queue
except ImportError:
    from queue import Queue
from threading import Thread
import unittest
import urllib

from yaksh.code_server import ServerPool, SERVER_POOL_PORT, submit, get_result
from yaksh import settings


class TestCodeServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        settings.code_evaluators['python']['standardtestcase'] = \
            "yaksh.python_assertion_evaluator.PythonAssertionEvaluator"
        server_pool = ServerPool(n=5, pool_port=SERVER_POOL_PORT)
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
        self.url = 'http://localhost:%s' % SERVER_POOL_PORT

    def test_infinite_loop(self):
        # Given
        testdata = {
            'metadata': {
                'user_answer': 'while True: pass',
                'language': 'python',
                'partial_grading': False
            },
            'test_case_data': [
                {'test_case': 'assert 1==2',
                 'test_case_type': 'standardtestcase',
                 'weight': 0.0}
            ]
        }

        # When
        submit(self.url, '0', json.dumps(testdata), '')
        result = get_result(self.url, '0')

        # Then
        self.assertTrue(result.get('status') in ['running', 'not started'])

        # When
        result = get_result(self.url, '0', block=True)

        # Then
        data = json.loads(result.get('result'))
        self.assertFalse(data['success'])
        self.assertTrue('infinite loop' in data['error'][0]['message'])

    def test_correct_answer(self):
        # Given
        testdata = {
            'metadata': {
                'user_answer': 'def f(): return 1',
                'language': 'python',
                'partial_grading': False
            },
            'test_case_data': [{'test_case': 'assert f() == 1',
                                'test_case_type': 'standardtestcase',
                                'weight': 0.0}]
        }

        # When
        submit(self.url, '0', json.dumps(testdata), '')
        result = get_result(self.url, '0', block=True)

        # Then
        data = json.loads(result.get('result'))
        self.assertTrue(data['success'])

    def test_wrong_answer(self):
        # Given
        testdata = {
            'metadata': {
                'user_answer': 'def f(): return 1',
                'language': 'python',
                'partial_grading': False
            },
            'test_case_data': [{'test_case': 'assert f() == 2',
                                'test_case_type': 'standardtestcase',
                                'weight': 0.0}]
        }

        # When
        submit(self.url, '0', json.dumps(testdata), '')
        result = get_result(self.url, '0', block=True)

        # Then
        data = json.loads(result.get('result'))
        self.assertFalse(data['success'])
        self.assertTrue('AssertionError' in data['error'][0]['exception'])

    def test_question_with_no_testcases(self):
        # Given
        testdata = {
            'metadata': {
                'user_answer': 'def f(): return 1',
                'language': 'python',
                'partial_grading': False
            },
            'test_case_data': []
        }

        # When
        submit(self.url, '0', json.dumps(testdata), '')
        result = get_result(self.url, '0', block=True)

        # Then
        data = json.loads(result.get('result'))
        self.assertFalse(data['success'])

        # With correct answer and test case
        testdata["metadata"]["user_answer"] = 'def f(): return 2'
        testdata["test_case_data"] = [{'test_case': 'assert f() == 2',
                                       'test_case_type': 'standardtestcase',
                                       'weight': 0.0
                                       }]
        # When
        submit(self.url, '0', json.dumps(testdata), '')
        result = get_result(self.url, '0', block=True)

        # Then
        data = json.loads(result.get('result'))
        self.assertTrue(data['success'])

    def test_multiple_simultaneous_hits(self):
        # Given
        results = Queue()

        def run_code(uid):
            """Run an infinite loop."""
            testdata = {
                'metadata': {
                    'user_answer': 'while True: pass',
                    'language': 'python',
                    'partial_grading': False
                },
                'test_case_data': [{'test_case': 'assert 1==2',
                                    'test_case_type': 'standardtestcase',
                                    'weight': 0.0}]
            }
            submit(self.url, uid, json.dumps(testdata), '')
            result = get_result(self.url, uid, block=True)
            results.put(json.loads(result.get('result')))

        N = 10
        # When
        threads = []
        for i in range(N):
            t = Thread(target=run_code, args=(str(i),))
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
            self.assertTrue('infinite loop' in data['error'][0]['message'])

    def test_server_pool_status(self):
        # Given
        url = "http://localhost:%s/" % SERVER_POOL_PORT

        # When
        response = urllib.request.urlopen(url)
        data = response.read().decode('utf-8')

        # Then
        expect = '5 processes, 0 running, 0 queued'
        self.assertTrue(expect in data)

    def test_killing_process_revives_it(self):
        # Given
        testdata = {
            'metadata': {
                'user_answer': 'import sys; sys.exit()',
                'language': 'python',
                'partial_grading': False
            },
            'test_case_data': [{'test_case': '',
                                'test_case_type': 'standardtestcase',
                                'weight': 0.0}]
        }

        # When
        submit(self.url, '0', json.dumps(testdata), '')
        result = get_result(self.url, '0', block=True)

        # Then
        data = json.loads(result.get('result'))
        self.assertFalse(data['success'])
        self.assertTrue('Process ended with exit code' in data['error'][0])

        # Now check the server status to see if the right number
        # processes are running.
        url = "http://localhost:%s/" % SERVER_POOL_PORT

        # When
        response = urllib.request.urlopen(url)
        data = response.read().decode('utf-8')

        # Then
        expect = '5 processes, 0 running, 0 queued'
        self.assertTrue(expect in data)


if __name__ == '__main__':
    unittest.main()
