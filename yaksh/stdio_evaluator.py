class Evaluator(object):

    def evaluate(self, user_answer, proc, expected_input, expected_output):
        success = False
        ip = expected_input.replace(",", " ")
        user_output, output_err = proc.communicate(input='{0}\n'.format(ip))
        expected_output = expected_output.replace("\r", "")
        if not expected_input:
            error_msg = "Expected Output is {0} ".\
                        format(repr(expected_output))
        else:
            error_msg = " Given Input is\n {0} \n Expected Output is {1} ".\
                        format(expected_input, repr(expected_output))
        if output_err == '':
            if user_output == expected_output:
                success, err = True, "Correct Answer"
            else:
                err = " Incorrect Answer\n" + error_msg +\
                      "\n Your output is {0}".format(repr(user_output))
        else:
            err = "Error:"+"\n"+output_err
        return success, err
