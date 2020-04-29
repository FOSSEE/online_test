"use strict";

function array_to_string(arr) {
    // returns comma separate values from the array
    return arr.join(", ");
}

function array_to_printable_string(arr) {
    var printable = []
    for (var e of arr) {
        if (e.startsWith('"') && e.endsWith('"')) {
            printable.push(e.slice(1, -1));
        }
        else {
            printable.push(e);
        }
    }
    return printable.join(", ");
}

function testcase(inputs, output) {
    this.inputs = array_to_string(inputs);
    this.printable_inputs = array_to_printable_string(inputs);
    this.output = output;
    this.content = "";
}

function testcases_info(language, function_name, no_of_input, input_types,
        output_type, testcases) {
    this.language = language
    this.function_name = function_name;
    this.no_of_input = no_of_input;
    this.input_types = array_to_string(input_types);
    this.output_type = output_type;
    this.testcases = testcases;
    this.tc_content = "";
}

testcases_info.prototype.add_testcase = function (inputs, output) {
    var tc = new testcase(inputs, output);
    this.testcases.push(tc);
}

testcases_info.prototype.generate_testcase_java = function () {
    for (var testcase of this.testcases) {
    var template = `
       result = t.${this.function_name}(${testcase.inputs});
       System.out.println(
            "Input submitted to the function: ${testcase.printable_inputs}");
       check(result, ${testcase.output});
    `;
    this.tc_content += template;
    }
}

testcases_info.prototype.generate_java = function () {
    var template = `
class main
{
    public static <E> void check(E expect, E result)
    {
        if(result.equals(expect))
        {
            System.out.println("Correct:Output expected "+expect+
                                "and got "+result);
        }
    else
    {
        System.out.println("Incorrect:Output expected "+expect+
                            "but got "+result);
        System.exit(1);
    }
    }
    public static void main(String arg[])
    {
       Test t = new Test();
       ${this.output_type} result;
       ${this.tc_content};
    }
}`;    
    this.content = template;
}

testcases_info.prototype.generate_testcase_c = function () {
    for (var testcase of this.testcases) {
    var template = `
    result = ${this.function_name}(${testcase.inputs});
    printf("Input submitted to the function: ${testcase.printable_inputs}\\n");
    check(${testcase.output}, result);
    `;
    this.tc_content += template;
    }
}

testcases_info.prototype.generate_c = function () {
    var template = `
#include <stdio.h>
#include <stdlib.h>

extern ${this.output_type} ${this.function_name}(${this.input_types});

template <class T>
void check(T expect,T result)
{
    if (expect == result)
    {
  printf("\\nCorrect:\\n Expected %d got %d \\n",expect,result);
    }
    else 
    {
  printf("\\nIncorrect:\\n Expected %d got %d \\n",expect,result);
  exit (1);
   }
}

int main(void)
{
  ${this.output_type} result;
  ${this.tc_content}
  printf("All Correct\\n");
}
    `;

    this.content = template;
}

testcases_info.prototype.generate_testcase_scilab = function () {
    for (var testcase of this.testcases) {
    var template = `
p = ${this.function_name}(${testcase.inputs});
correct = (p == ${testcase.output});
if correct then
 i=3;
else
 i=0;
end
disp("Input submitted ${testcase.printable_inputs}")
disp("Expected output "+ string(${testcase.output}) + "got " + string(p))
    `;
    this.tc_content += template;
    }
}

testcases_info.prototype.generate_scilab = function () {
    var template = `
mode(-1)
exec("function.sci",-1);
i = 0
${this.tc_content}
if i==3 then
 exit(5);
else
 exit(3);
end
`;    
    this.content = template;
}

testcases_info.prototype.generate_testcase_r = function () {
    for (var testcase of this.testcases) {
    var template = `
result = ${this.function_name}(${testcase.inputs})
print("Input submitted ${testcase.printable_inputs}")
check(result, ${testcase.output})
    `;
    this.tc_content += template;
    }
}

testcases_info.prototype.generate_r = function () {
    var template = `
source("function.r")
check_empty = function(obj){
    stopifnot(is.null(obj) == FALSE)
}
check = function(output, expect){
cat("Excepted output", expect, "got ",output, "/n")
stopifnot(expect == output)
}
is_correct = function(){
if (count == 3){
    quit("no", 31)
}
}
check_empty(${this.function_name}(${this.testcases[0].inputs}))
count = 3
${this.tc_content}
is_correct()
`;    
    this.content = template;
}

function get_testcase_info(lang, fname, num_in, itypes, otype, testcases) {
    var tc_in = new testcases_info(lang, fname, num_in, itypes, otype, testcases);
    return tc_in
}

testcases_info.prototype.generate = function() {
    if (this.language == 'C' || this.language == 'C++') {
        this.generate_testcase_c();
        this.generate_c();
    }
    else if (this.language == 'Java') {
        this.generate_testcase_java();
        this.generate_java();
    }
    else if (this.language == 'Scilab') {
        this.generate_testcase_scilab();
        this.generate_scilab();
    }
    else if (this.language == 'R') {
        this.generate_testcase_r();
        this.generate_r();
    }
}
