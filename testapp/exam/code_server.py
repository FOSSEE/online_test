#!/usr/bin/env python
"""This server runs an XMLRPC server that can be submitted code and tests
and returns the output.  It *should* be run as root and will run as the user
'nobody' so as to minimize any damange by errant code.  This can be configured
by editing settings.py to run as many servers as desired.  One can also
specify the ports on the command line.  Here are examples::

  $ sudo ./code_server.py
  # Runs servers based on settings.py:SERVER_PORTS one server per port given.

or::

  $ sudo ./code_server.py 8001 8002 8003 8004 8005
  # Runs 5 servers on ports specified.

All these servers should be running as nobody.  This will also start a server
pool that defaults to port 50000 and is configurable in
settings.py:SERVER_POOL_PORT.  This port exposes a `get_server_port` function
that returns an available server.
"""
import sys
import traceback
from SimpleXMLRPCServer import SimpleXMLRPCServer
import pwd
import os
import stat
from os.path import isdir, dirname, abspath, join, isfile
import signal
from multiprocessing import Process, Queue
import subprocess
import re
import json
# Local imports.
from settings import SERVER_PORTS, SERVER_TIMEOUT, SERVER_POOL_PORT

MY_DIR = abspath(dirname(__file__))


def run_as_nobody():
    """Runs the current process as nobody."""
    # Set the effective uid and to that of nobody.
    nobody = pwd.getpwnam('nobody')
    os.setegid(nobody.pw_gid)
    os.seteuid(nobody.pw_uid)


# Raised when the code times-out.
# c.f. http://pguides.net/python/timeout-a-function
class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    """A handler for the ALARM signal."""
    raise TimeoutException('Code took too long to run.')

def create_signal_handler():
    """Add a new signal handler for the execution of this code."""
    prev_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(SERVER_TIMEOUT)
    return prev_handler

def set_original_signal_handler(old_handler=None):
    """Set back any original signal handler."""
    if old_handler is not None:
        signal.signal(signal.SIGALRM, old_handler)
        return
    else:
        raise Exception("Signal Handler: object cannot be NoneType")

def delete_signal_handler():
    signal.alarm(0)
    return



###############################################################################
# `TestCode` class.
###############################################################################
class TestCode(object):
    """Evaluates and tests the code obtained from Code Server"""
    def __init__(self, test_parameter, language, user_answer, ref_code_path=None, in_dir=None):
        self.test_parameter = test_parameter
        self.language = language
        self.user_answer = user_answer
        self.ref_code_path = ref_code_path
        self.in_dir = in_dir

    def run_code(self):
        """Tests given code  (`answer`) with the test cases based on
        given arguments.

        The ref_code_path is a path to the reference code.
        The reference code will call the function submitted by the student.
        The reference code will check for the expected output.

        If the path's start with a "/" then we assume they are absolute paths.
        If not, we assume they are relative paths w.r.t. the location of this
        code_server script.

        If the optional `in_dir` keyword argument is supplied it changes the
        directory to that directory (it does not change it back to the original
        when done).

        Returns
        -------

        A tuple: (success, error message).
        """
        success = False
        prev_handler = None

        self._change_dir(self.in_dir)

        if self.language == "python":
            tb = None
            test_code = self.create_test_case()
            # Add a new signal handler for the execution of this code.
            prev_handler = create_signal_handler()

            try:
                submitted = compile(self.user_answer, '<string>', mode='exec')
                g = {}
                exec submitted in g
                _tests = compile(test_code, '<string>', mode='exec')
                exec _tests in g
            except TimeoutException:
                err = self.timeout_msg
            except AssertionError:
                type, value, tb = sys.exc_info()
                info = traceback.extract_tb(tb)
                fname, lineno, func, text = info[-1]
                text = str(test_code).splitlines()[lineno-1]
                err = "{0} {1} in: {2}".format(type.__name__, str(value), text)
            except:
                type, value = sys.exc_info()[:2]
                err = "Error: {0}".format(repr(value))
            else:
                success = True
                err = 'Correct answer'
            finally:
                del tb
                # Set back any original signal handler.
                set_original_signal_handler(prev_handler)

            # Cancel the signal
            delete_signal_handler()

        else:
            user_answer_file = {'C': 'submit.c', 'java': 'Test.java', 'scilab': 'function.sci',
                                    'C++': 'submitstd.cpp', 'bash': 'submit.sh'}

            # File extension depending on the question language
            submit_f = open(user_answer_file.get(self.language), 'w')
            submit_f.write(self.user_answer.lstrip())
            submit_f.close()
            submit_path = abspath(submit_f.name)
            if self.language == "bash":
                self._set_exec(submit_path)

            path_list = self.ref_code_path.split(',')
            ref_path = path_list[0].strip() if path_list[0] else ""
            test_case_path = path_list[1].strip() if path_list[1] else ""
            if ref_path and not ref_path.startswith('/'):
                ref_path = join(MY_DIR, ref_path)
            if test_case_path and not test_case_path.startswith('/'):
                test_case_path = join(MY_DIR, test_case_path)

            if self.language in ["C++", "C", "java"]:
                # Add a new signal handler for the execution of this code.
                prev_handler = create_signal_handler()

                # Do whatever testing needed.
                try:
                    success, err = self._check_code(ref_path, submit_path)
                except TimeoutException:
                    err = self.timeout_msg
                except:
                    type, value = sys.exc_info()[:2]
                    err = "Error: {0}".format(repr(value))
                finally:
                    # Set back any original signal handler.
                    set_original_signal_handler(prev_handler)

            elif self.language == "scilab":
                # Add a new signal handler for the execution of this code.
                prev_handler = create_signal_handler()

                # Do whatever testing needed.
                try:
                    cmd = 'printf "lines(0)\nexec(\'{0}\',2);\nquit();"'.format(ref_path)
                    cmd += ' | timeout 8 scilab-cli -nb'
                    ret = self._run_command(cmd,
                                            shell=True,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                    proc, stdout, stderr = ret

                    # Get only the error.
                    stderr = self._get_error(stdout)
                    if stderr is None:
                        # Clean output
                        stdout = self._strip_output(stdout)
                        if proc.returncode == 5:
                            success, err = True, "Correct answer"
                        else:
                            err = add_err + stdout
                    else:
                        err = add_err + stderr
                except TimeoutException:
                    err = self.timeout_msg
                except:
                    type, value = sys.exc_info()[:2]
                    err = "Error: {0}".format(repr(value))
                finally:
                    # Set back any original signal handler.
                    set_original_signal_handler(prev_handler)

            elif self.language == "bash":
                # Add a new signal handler for the execution of this code.
                prev_handler = create_signal_handler()

                try:
                    success, err = self.check_bash_script(ref_path, submit_path,
                                                          test_case_path)
                except TimeoutException:
                    err = self.timeout_msg
                except:
                    type, value = sys.exc_info()[:2]
                    err = "Error: {0}".format(repr(value))
                finally:
                    # Set back any original signal handler.
                    set_original_signal_handler(prev_handler)

            # Delete the created file.
            os.remove(submit_path)

            # Cancel the signal
            delete_signal_handler()

        result = {'success': success, 'error': err}
        return result

    def _check_code(self, ref_code_path, submit_code_path):
        """ Function validates student code using instructor code as
        reference.The first argument ref_code_path, is the path to
        instructor code, it is assumed to have executable permission.
        The second argument submit_code_path, is the path to the student
        code, it is assumed to have executable permission.

        Returns
        --------

        returns (True, "Correct answer") : If the student function returns
        expected output when called by reference code.

        returns (False, error_msg): If the student function fails to return
        expected output when called by reference code.

        Returns (False, error_msg): If mandatory arguments are not files or
        if the required permissions are not given to the file(s).

        """

        language_dependent_path = {
            'c_user_output_path': os.getcwd() +  '/output',
            'c_ref_output_path': os.getcwd() + '/executable',
            'java_student_directory': os.getcwd() + '/',
            # 'java_student_file_name': 'Test',
            'java_ref_file_name': (ref_code_path.split('/')[-1]).split('.')[0],
        }

        language_dependent_var = {
            'C': {'compile_command': 'g++  {0} -c -o {1}'.format(submit_code_path,
                        language_dependent_path.get('c_user_output_path')),
                    'compile_main': 'g++ {0} {1} -o {2}'.format(ref_code_path,
                        language_dependent_path.get('c_user_output_path'),
                        language_dependent_path.get('c_ref_output_path')),
                    'run_command_args': [language_dependent_path.get('c_ref_output_path')],
                    'remove_user_output': language_dependent_path.get('c_user_output_path'),
                    'remove_ref_output': language_dependent_path.get('c_ref_output_path')
                },
            'java':{'compile_command': 'javac  {0}'.format(submit_code_path),
                    'compile_main': 'javac {0} -classpath {1} -d {2}'.format(ref_code_path,
                        language_dependent_path.get('java_student_directory'),
                        language_dependent_path.get('java_student_directory')),
                    'run_command_args': "java -cp {0} {1}".format(
                        language_dependent_path.get('java_student_directory'),
                        language_dependent_path.get('java_ref_file_name')),
                    'remove_user_output': "%s%s.class".format(
                        language_dependent_path.get('java_student_directory'),
                        'Test'),
                    'remove_ref_output': "%s%s.class".format(
                        language_dependent_path.get('java_student_directory'),
                        language_dependent_path.get('java_ref_file_name')),
                }
        }

        if not isfile(ref_code_path):
            return False, "No file at %s or Incorrect path" % ref_code_path
        if not isfile(submit_code_path):
            return False, 'No file at %s or Incorrect path' % submit_code_path

        success = False
        # output_path = os.getcwd() + '/output'
        compile_command = language_dependent_var.get(self.language).get('compile_command') # "g++  %s -c -o %s" % (submit_code_path, output_path)
        ret = self._compile_command(compile_command)
        proc, stdnt_stderr = ret
        if self.language == "java":
            stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)

        # Only if compilation is successful, the program is executed
        # And tested with testcases
        if stdnt_stderr == '':
            compile_main = language_dependent_var.get(self.language).get('compile_main') # "g++ %s %s -o %s" % (ref_code_path, output_path, executable)
            ret = self._compile_command(compile_main)
            proc, main_err = ret
            if self.language == "java":
                main_err = self._remove_null_substitute_char(main_err)

            if main_err == '':
                run_command_args = language_dependent_var.get(self.language).get('run_command_args')
                ret = self._run_command(run_command_args, stdin=None,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                proc, stdout, stderr = ret
                if proc.returncode == 0:
                    success, err = True, "Correct answer"
                else:
                    err = stdout + "\n" + stderr
                os.remove(language_dependent_var.get(self.language).get('remove_ref_output')) # os.remove(executable)
            else:
                err = "Error:"
                try:
                    error_lines = main_err.splitlines()
                    for e in error_lines:
                        if ':' in e:
                            err = err + "\n" + e.split(":", 1)[1]
                        else:
                            err = err + "\n" + e
                except:
                        err = err + "\n" + main_err
            os.remove(language_dependent_var.get(self.language).get('remove_user_output')) # os.remove(output_path)
        else:
            err = "Compilation Error:"
            try:
                error_lines = stdnt_stderr.splitlines()
                for e in error_lines:
                    if ':' in e:
                        err = err + "\n" + e.split(":", 1)[1]
                    else:
                        err = err + "\n" + e
            except:
                err = err + "\n" + stdnt_stderr

        result = {'success': success, 'error': err}
        return result

    def check_bash_script(self, ref_path, submit_path,
                          test_case_path=None):
        """ Function validates student script using instructor script as
        reference. Test cases can optionally be provided.  The first argument
        ref_path, is the path to instructor script, it is assumed to
        have executable permission.  The second argument submit_path, is
        the path to the student script, it is assumed to have executable
        permission.  The Third optional argument is the path to test the
        scripts.  Each line in this file is a test case and each test case is
        passed to the script as standard arguments.

        Returns
        --------

        returns (True, "Correct answer") : If the student script passes all
        test cases/have same output, when compared to the instructor script

        returns (False, error_msg): If the student script fails a single
        test/have dissimilar output, when compared to the instructor script.

        Returns (False, error_msg): If mandatory arguments are not files or if
        the required permissions are not given to the file(s).

        """
        if not isfile(ref_path):
            return False, "No file at %s or Incorrect path" % ref_path
        if not isfile(submit_path):
            return False, "No file at %s or Incorrect path" % submit_path
        if not os.access(ref_path, os.X_OK):
            return False, "Script %s is not executable" % ref_path
        if not os.access(submit_path, os.X_OK):
            return False, "Script %s is not executable" % submit_path

        if test_case_path is None or "":
            ret = self._run_command(ref_path, stdin=None,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc, inst_stdout, inst_stderr = ret
            ret = self._run_command(submit_path, stdin=None,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc, stdnt_stdout, stdnt_stderr = ret
            if inst_stdout == stdnt_stdout:
                return True, "Correct answer"
            else:
                err = "Error: expected %s, got %s" % (inst_stderr,
                                                      stdnt_stderr)
                return False, err
        else:
            if not isfile(test_case_path):
                return False, "No test case at %s" % test_case_path
            if not os.access(ref_path, os.R_OK):
                return False, "Test script %s, not readable" % test_case_path
            valid_answer = True  # We initially make it one, so that we can
                                 # stop once a test case fails
            loop_count = 0  # Loop count has to be greater than or
                            # equal to one.
                            # Useful for caching things like empty
                            # test files,etc.
            test_cases = open(test_case_path).readlines()
            num_lines = len(test_cases)
            for test_case in test_cases:
                loop_count += 1
                if valid_answer:
                    args = [ref_path] + [x for x in test_case.split()]
                    ret = self._run_command(args, stdin=None,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                    proc, inst_stdout, inst_stderr = ret
                    args = [submit_path]+[x for x in test_case.split()]
                    ret = self._run_command(args, stdin=None,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                    proc, stdnt_stdout, stdnt_stderr = ret
                    valid_answer = inst_stdout == stdnt_stdout
            if valid_answer and (num_lines == loop_count):
                return True, "Correct answer"
            else:
                err = "Error:expected %s, got %s" % (inst_stdout+inst_stderr,
                                                     stdnt_stdout+stdnt_stderr)
                return False, err

    def _run_command(self, cmd_args, *args, **kw):
        """Run a command in a subprocess while blocking, the process is killed
        if it takes more than 2 seconds to run.  Return the Popen object, the
        stdout and stderr.
        """
        try:
            proc = subprocess.Popen(cmd_args, *args, **kw)
            stdout, stderr = proc.communicate()
        except TimeoutException:
            # Runaway code, so kill it.
            proc.kill()
            # Re-raise exception.
            raise
        return proc, stdout, stderr

    def _compile_command(self, cmd, *args, **kw):
        """Compiles C/C++/java code and returns errors if any.
        Run a command in a subprocess while blocking, the process is killed
        if it takes more than 2 seconds to run.  Return the Popen object, the
        stderr.
        """
        try:
            proc_compile = subprocess.Popen(cmd, shell=True, stdin=None,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
            out, err = proc_compile.communicate()
        except TimeoutException:
            # Runaway code, so kill it.
            proc_compile.kill()
            # Re-raise exception.
            raise
        return proc_compile, err

    def _remove_null_substitute_char(self, string):
        """Returns a string without any null and substitute characters"""
        stripped = ""
        for c in string:
            if ord(c) is not 26 and ord(c) is not 0:
                stripped = stripped + c
        return ''.join(stripped)

    def _remove_scilab_exit(self, string):
        """
            Removes exit, quit and abort from the scilab code
        """
        new_string = ""
        i=0
        for line in string.splitlines():
            new_line = re.sub(r"exit.*$","",line)
            new_line = re.sub(r"quit.*$","",new_line)
            new_line = re.sub(r"abort.*$","",new_line)
            if line != new_line:
                i=i+1
            new_string = new_string +'\n'+ new_line
        return new_string, i

    def _get_error(self, string):
        """
            Fetches only the error from the string.
            Returns None if no error.
        """
        obj =  re.search("!.+\n.+",string);
        if obj:
            return obj.group()
        return None

    def _strip_output(self, out):
        """
            Cleans whitespace from the output
        """
        strip_out = "Message"
        for l in out.split('\n'):
            if l.strip():
                strip_out = strip_out+"\n"+l.strip()
        return strip_out

    def _set_exec(self, fname):
        os.chmod(fname,  stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
                 | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
                 | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)

    def create_test_case(self):
        """ 
            Create assert based test cases in python 
        """
        if self.language == "python":
            test_code = ""
            for test_case in self.test_parameter:
                pos_args = ", ".join(str(i) for i in test_case.get('pos_args')) if test_case.get('pos_args') \
                                else ""
                kw_args = ", ".join(str(k+"="+a) for k, a in test_case.get('kw_args').iteritems()) \
                                if test_case.get('kw_args') else ""
                args = pos_args + ", " + kw_args if pos_args and kw_args else pos_args or kw_args
                tcode = "assert {0}({1}) == {2}" \
                    .format(test_case.get('func_name'), args, test_case.get('expected_answer'))
                test_code += tcode + "\n"
            return test_code

    def _change_dir(self, in_dir):
        if in_dir is not None and isdir(in_dir):
            os.chdir(in_dir)


###############################################################################
# `CodeServer` class.
###############################################################################
class CodeServer(object):
    """A code server that executes user submitted test code, tests it and
    reports if the code was correct or not.
    """
    def __init__(self, port, queue):
        self.port = port
        self.queue = queue
        msg = 'Code took more than %s seconds to run. You probably '\
              'have an infinite loop in your code.' % SERVER_TIMEOUT
        self.timeout_msg = msg

    def checker(self, info_parameter, in_dir=None):
        """Calls the TestCode Class to test the current code"""
        info_parameter = json.loads(info_parameter)
        test_parameter = info_parameter.get("test_parameter")
        language = info_parameter.get("language")
        user_answer = info_parameter.get("user_answer")
        ref_code_path = info_parameter.get("ref_code_path")

        tc = TestCode(test_parameter, language, user_answer, ref_code_path, in_dir)
        result = tc.run_code()
        # Put us back into the server pool queue since we are free now.
        self.queue.put(self.port)

        return json.dumps(result)

    def run(self):
        """Run XMLRPC server, serving our methods."""
        server = SimpleXMLRPCServer(("localhost", self.port))
        self.server = server
        server.register_instance(self)
        self.queue.put(self.port)
        server.serve_forever()


###############################################################################
# `ServerPool` class.
###############################################################################
class ServerPool(object):
    """Manages a pool of CodeServer objects."""
    def __init__(self, ports, pool_port=50000):
        """Create a pool of servers.  Uses a shared Queue to get available
        servers.

        Parameters
        ----------

        ports : list(int)
            List of ports at which the CodeServer's should run.

        pool_port : int
            Port at which the server pool should serve.
        """
        self.my_port = pool_port
        self.ports = ports
        queue = Queue(maxsize=len(ports))
        self.queue = queue
        servers = []
        for port in ports:
            server = CodeServer(port, queue)
            servers.append(server)
            p = Process(target=server.run)
            p.start()
        self.servers = servers

    def get_server_port(self):
        """Get available server port from ones in the pool.  This will block
        till it gets an available server.
        """
        q = self.queue
        was_waiting = True if q.empty() else False
        port = q.get()
        if was_waiting:
            print '*'*80
            print "No available servers, was waiting but got server \
                   later at %d." % port
            print '*'*80
            sys.stdout.flush()
        return port

    def run(self):
        """Run server which returns an available server port where code
        can be executed.
        """
        server = SimpleXMLRPCServer(("localhost", self.my_port))
        self.server = server
        server.register_instance(self)
        server.serve_forever()


###############################################################################
def main():
    run_as_nobody()
    if len(sys.argv) == 1:
        ports = SERVER_PORTS
    else:
        ports = [int(x) for x in sys.argv[1:]]

    server_pool = ServerPool(ports=ports, pool_port=SERVER_POOL_PORT)
    server_pool.run()

if __name__ == '__main__':
    main()
