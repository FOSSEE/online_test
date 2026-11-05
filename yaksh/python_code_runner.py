"""Run student's code and capture what it prints

'Run' button for code questions. Question not graded,
simply runs the code with optional standard input, and
returns everything written to stdout and stderr for students to see it.

Runs as a separate Python process.
"""

import re
import os
import subprocess
import selectors
import signal
import shutil
import time
import tempfile
import sys

from .file_utils import copy_files, delete_files
from .settings import SERVER_TIMEOUT

SCRIPT_NAME = 'main.py'
MAX_OUTPUT_CHARS = 10000
MAX_INPUT_CHARS = 10000
_READ_CHUNK = 4096
_MAX_OUTPUT_BYTES = MAX_OUTPUT_CHARS * 4
_ERROR_LINE_RE = re.compile(r'File "{0}", line (\d+)'.format(SCRIPT_NAME))
_NEEDS_INPUT_HINT = ('Your program needs input, type it in the Input box and '
                     'run again.')


class PythonCodeRunner(object):
    def __init__(self, metadata, timeout=None):
        self.user_answer = metadata.get('user_answer') or ''
        self.stdin = (metadata.get('stdin') or '')[:MAX_INPUT_CHARS]
        self.file_paths = metadata.get('file_paths')
        self.timeout = timeout if timeout is not None else SERVER_TIMEOUT
        self.files = []

    def run(self):
        """Run the code in the directory and return a dict with:

        output      -- combined stdout and stderr
        exit_code   -- procees exitcode, None if it was killed on timeout
        truncated   -- True if outputput is cut after MAX_OUTPUT_CHARS
        timed_out   -- True if code ran more than timeout
        error_line  -- line where an error occured
        hint        -- optional feedback for the student

        """

        if self.file_paths:
            self.files  = copy_files(self.file_paths)
        work_dir = tempfile.mkdtemp(prefix='run_', dir=os.getcwd())
        script_path = os.path.join(work_dir, SCRIPT_NAME)
        try:
            with open(script_path, 'w') as f:
                f.write(self.user_answer)
            raw, exit_code, timed_out, truncated = self._execute(script_path)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
            if self.files:
                delete_files(self.files)
        output = raw.decode('utf-8', 'replace').replace(script_path,
                                                        SCRIPT_NAME)
        if len(output) > MAX_OUTPUT_CHARS:
                output = output[:MAX_OUTPUT_CHARS]
                truncated = True
        error_line = None
        hint = None
        if exit_code not in (0, None):
            matches = _ERROR_LINE_RE.findall(output)
            if matches:
                error_line = int(matches[-1])
            if 'EOFError' in output and not self.stdin:
                hint = _NEEDS_INPUT_HINT
        return {'output': output, 'exit_code': exit_code,
                'timed_out': timed_out, 'truncated': truncated,
                'error_line': error_line, 'hint': hint,}

    def _execute(self, script_path):
        # -u keeps stdio and stderr in the order as written
        # -E -s Ignore PYTHON* variables and user site directory
        # The working directory stays the user's directory, so that the
        # files attached to the questions can be opened and imported.

        cmd = [sys.executable, '-u', '-E' , '-s', script_path]
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, preexec_fn=os.setpgrp
        )
        try:
            try:
                proc.stdin.write(self.stdin.encode('utf-8'))
            except BrokenPipeError:
                pass
            try:
                proc.stdin.close()
            except BrokenPipeError:
                pass
            return self._read_output(proc)
        finally:
            self._kill(proc)

    def _read_output(self, proc):
        deadline = time.monotonic() + self.timeout
        chunks = []
        size = 0
        timed_out = truncated = False
        fd = proc.stdout.fileno()
        with selectors.DefaultSelector() as selector:
            selector.register(fd, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    break
                if not selector.select(remaining):
                    continue
                data = os.read(fd, _READ_CHUNK)
                if not data:
                    break
                chunks.append(data[:_MAX_OUTPUT_BYTES - size])
                size += len(data)
                if size >= _MAX_OUTPUT_BYTES:
                    truncated = True
                    break
        if not timed_out and not truncated:
            try:
                proc.wait(max(deadline - time.monotonic(), 0))
            except subprocess.TimeoutExpired:
                timed_out = True
        exit_code = None if timed_out else proc.poll()
        return b''.join(chunks), exit_code, timed_out, truncated

    @staticmethod
    def _kill(proc):
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (PermissionError, ProcessLookupError):
                proc.kill()
        proc.wait()
        proc.stdout.close()

