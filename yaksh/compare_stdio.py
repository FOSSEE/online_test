try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

class CompareOutputs(object):
	
	def _incorrect_user_lines(self, exp_lines, user_lines):
	    err_line_no = []
	    for i, (expected_line, user_line) in enumerate(zip_longest(exp_lines, user_lines)):
	        if not user_line or not expected_line:
	            err_line_no.append(i)
	        else:
	            if user_line.strip() != expected_line.strip():
	                err_line_no.append(i)
	    return err_line_no
	
	def compare_outputs(self, expected_output, user_output,given_input=None):
	    given_lines = user_output.splitlines()
	    exp_lines = expected_output.splitlines()
	    # if given_input:
	    #     given_input =  given_input.splitlines()
	    msg = {"given_input":given_input,
	           "expected_output": exp_lines,
	           "user_output":given_lines
	            }
	    ng = len(given_lines)
	    ne = len(exp_lines)
	    if ng != ne:
	        err_line_no = self._incorrect_user_lines(exp_lines, given_lines)
	        msg["error_no"] = err_line_no
	        msg["error"] = "Incorrect Answer: We had expected {0} number of lines. We got {1} number of lines.".format(ne, ng)
	        return False, msg
	    else:
	        err_line_no = self._incorrect_user_lines(exp_lines, given_lines)
	        if err_line_no:
	            msg["error_no"] = err_line_no
	            msg["error"] = "Incorrect Answer: Line number(s) {0} did not match."\
	                            .format(", ".join(map(str,[x+1 for x in err_line_no])))
	            return False, msg
	        else:
	            msg["error"] = "Correct answer"
	            return True, msg
