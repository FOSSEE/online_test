import unittest
import tempfile
import shutil
import textwrap
import os

from yaksh.grader import Grader
from yaksh.python_code_runner import MAX_OUTPUT_CHARS, PythonCodeRunner

class PythonCodeRunnerTestCase(unittest.TestCase):
    def setUp(self):
        self.in_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.in_dir)

    def run_code(self, code, stdin='', file_paths=None, language='python',
                 show_lines=False):
        kwargs = {
            'metadata': {
                'user_answer': code, 'stdin': stdin, 'language': language,
                'file_paths': file_paths, 'partial_grading': False,
                'run_only': True, 'show_lines': show_lines,
            },
            'test_case_data': [],
        }
        return Grader(self.in_dir).evaluate(kwargs)

    def test_print_output_is_returned(self):
        # Given
        code = textwrap.dedent("""
            a = [1, 2]
            print(a)
            print('total', sum(a))
        """)

        # When
        result = self.run_code(code)

        # Then
        self.assertEqual(result['output'], "[1, 2]\ntotal 3\n")
        self.assertEqual(result['exit_code'], 0)
        self.assertFalse(result['timed_out'])
        self.assertIsNone(result['error_line'])

    def test_stdout_and_stderr_keep_their_order(self):
        # Given
        code = textwrap.dedent("""
            import sys
            print('one')
            print('two', file=sys.stderr)
            print('three')
        """)

        # When
        result = self.run_code(code)

        # Then
        self.assertEqual(result['output'], "one\ntwo\nthree\n")

    def test_runtime_error_shows_traceback_and_line(self):
        # Given
        code = textwrap.dedent("""\
            print('before')
            x = 1/0
        """)

        # When
        result = self.run_code(code)

        # Then
        self.assertEqual(result['exit_code'], 1)
        self.assertTrue(result['output'].startswith('before\n'))
        self.assertIn('File "main.py", line 2', result['output'])
        self.assertIn('ZeroDivisionError', result['output'])
        self.assertEqual(result['error_line'], 2)
        # The temporary path of the script is not shown
        self.assertNotIn(self.in_dir, result['output'])

    def test_syntax_error(self):
        # Given
        code = textwrap.dedent("""\
            x = 1
            def f(:
                pass
        """)

        # When
        result = self.run_code(code)

        # Then
        self.assertEqual(result['exit_code'], 1)
        self.assertIn('SyntaxError', result['output'])
        self.assertEqual(result['error_line'], 2)

    def test_stdin_is_passed_to_input(self):
        # Given
        code = textwrap.dedent("""
            n = int(input())
            print(n*2)
        """)
        stdin="21\n"

        # When
        result = self.run_code(code, stdin=stdin)

        # Then
        self.assertEqual(result['output'], "42\n")
        self.assertIsNone(result['hint'])

    def test_missing_input_gives_hint(self):
        # Given
        code = textwrap.dedent("""
            name = input()
            print(name)
        """)

        # When
        result = self.run_code(code)

        # Then
        self.assertIn('EOFError', result['output'])
        self.assertIn('Input box', result['hint'])

    def test_timeout_kills_code_catches_everything(self):
        # Given
        code = textwrap.dedent("""
            print("started")
            while True:
                try:
                    pass
                except BaseException:
                    pass
        """)

        # When
        with self._chdir():
            result = PythonCodeRunner({'user_answer': code},
                                              timeout=1).run()
        # Then
        self.assertTrue(result['timed_out'])
        self.assertIsNone(result['exit_code'])
        self.assertEqual(result['output'], 'started\n')

    def test_output_is_capped(self):
        # Given
        code = textwrap.dedent("""
            while True:
                print('a' * 100)
        """)

        # When
        result = self.run_code(code)

        # Then
        self.assertTrue(result['truncated'])
        self.assertLessEqual(len(result['output']), MAX_OUTPUT_CHARS)

    def test_exit_code_is_reported(self):
        # Given
        code = textwrap.dedent("""
            import sys
            print('bye')
            sys.exit(3)
        """)

        # When
        result = self.run_code(code)

        # Then
        self.assertEqual(result['output'], 'bye\n')
        self.assertEqual(result['exit_code'], 3)

    def test_question_files_can_be_read(self):
        # Given
        data_file = os.path.join(tempfile.mkdtemp(), 'data.txt')
        with open(data_file, 'w') as f:
            f.write('32')
        code = textwrap.dedent("""
            print(open('data.txt').read())
        """)

        # When
        try:
            result = self.run_code(code, file_paths=[(data_file, False)])
        finally:
            shutil.rmtree(os.path.dirname(data_file))

        # Then
        self.assertEqual(result['output'], "32\n")
        # Copied files are removed after run
        self.assertFalse(os.path.exists(os.path.join(self.in_dir, 'data.txt')))

    def test_no_files_left_behind(self):
        # Given
        code = textwrap.dedent("""
            print('hi')
        """)

        # when
        result = self.run_code(code)

        # Then
        self.assertEqual(os.listdir(self.in_dir), [])

    def test_unsupported_language(self):
        # Given
        code = "int main(){}"

        # When
        result = self.run_code(code, language='c')

        # Then
        self.assertEqual(result['output'], '')
        self.assertIn('not available', result['hint'])

    def test_call_on_its_own_line_shows_value(self):
        # Given
        code = textwrap.dedent("""\
            \"\"\"Adds two numbers.\"\"\"
            def add(a, b):
                return a + b

            add(2, 3)
            x = add(1, 1)
            print('x is', x)
            print(add(0, 0))
        """)

        # When
        result = self.run_code(code, show_lines=True)

        # Then: like the Python prompt, each line is shown before its
        # output; definitions, the docstring and None are not shown
        self.assertEqual(result['output'], textwrap.dedent("""\
            >>> add(2, 3)
            5
            >>> x = add(1, 1)
            >>> print('x is', x)
            x is 2
            >>> print(add(0, 0))
            0
        """))

        self.assertEqual(result['exit_code'], 0)

    def test_error_in_called_function(self):
        # Given
        code = textwrap.dedent("""\
            def average(numbers):
                return sum(numbers) / len(numbers)

            average([])
            average([2])
        """)

        # When
        result = self.run_code(code, show_lines=True)

        # Then: stops at the error; the loader's own frame is not shown
        output = result['output']
        self.assertTrue(output.startswith(
            ">>> average([])\nTraceback (most recent call last):\n"))
        self.assertIn('File "main.py", line 4, in <module>', output)
        self.assertIn('File "main.py", line 2, in average', output)
        self.assertIn('ZeroDivisionError', output)
        self.assertNotIn('<string>', output)
        self.assertNotIn('2.0', output)
        self.assertEqual(result['error_line'], 2)

    def test_calls_under_main_guard_show_values(self):
        # Given
        code = textwrap.dedent("""\
            def area(r):
                return 3 * r * r

            if __name__ == "__main__":
                area(2)
        """)

        # When
        result = self.run_code(code, show_lines=True)

        # Then: a block is shown with "... " lines, as at the prompt
        self.assertEqual(result['output'],
                         '>>> if __name__ == "__main__":\n'
                         '...     area(2)\n'
                         '12\n')

    def test_programs_run_as_they_are(self):
        # Given: a program for a stdio question (not show_lines)
        code = "x = 2 + 3\nx\nprint('done')\n"

        # When
        result = self.run_code(code)

        # Then: no ">>>" lines and no values, as with "python main.py"
        self.assertEqual(result['output'], "done\n")

    def _chdir(self):
        in_dir = self.in_dir

        class _ChDir(object):
            def __enter__(self):
                self.old = os.getcwd()
                os.chdir(in_dir)

            def __exit__(self, *args):
                os.chdir(self.old)
        return _ChDir()

if __name__ == '__main__':
    unittest.main()
