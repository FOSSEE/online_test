class Evaluator(object):

    def evaluate(self, user_answer, proc, expected_input, expected_output):
        success = False
        if expected_input:
            ip = expected_input.replace(",", " ")
            proc.stdin.write('{0}\n'.format(ip))
            error_msg = " Given Input is {0} \n Expected Output is {1} ".\
                        format(expected_input, expected_output)
        else:
            error_msg = "Expected output is {0}".format(expected_output)
        output_err = proc.stderr.read()
        user_output = proc.stdout.read()
        expected_output = expected_output.replace("\r", "")
        if output_err == '':
            if user_output == expected_output:
                success, err = True, "Correct Answer"
            else:
                err = " Incorrect Answer\n" + error_msg +\
                      "\n Your output is {0}".format(user_output)
        else:
            err = "Error:"+"\n"+output_err
        return success, err
