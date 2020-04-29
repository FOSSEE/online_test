"use strict"

const C_TYPES = ['int', 'float', 'char', 'double', 'bool']
const JAVA_TYPES = ['int', 'float', 'char', 'double', 'String', 'boolean']

function create_file_content() {
    var form = document.getElementById("tc_form");
    if (!validate(form.elements.languages)) { return false;}
    var language = form.elements.languages.value;
    if (!validate(form.elements.function_name)) { return false;}
    var fname = form.elements.function_name.value;
    if (!validate(form.elements.no_of_input)) { return false;}
    var num_in = form.elements.no_of_input.value;
    var input_types = form.getElementsByClassName("itypes");  
    var otype = form.elements.types_out.value;
    var itypes = [];
    for (var ele of input_types) {
        if (!validate(ele)) { return false;}
        itypes.push(ele.value);
    }
    var tcs = get_testcase_info(language, fname, num_in, itypes, otype, [])
    var testcases = document.getElementById("testcases");
    for (var x=1; x <= testcases.childElementCount; x++) {
        var inputs = [];
        var output = "";
            var ins = document.getElementsByClassName("tc_in_"+x)
            for (var i of ins) {
            if (!validate(i)) { return false;}
                inputs.push(i.value);
            }
            var output_ele = document.getElementById("out"+x)
            if (!validate(output_ele)) { return false;}
            output = output_ele.value;
            tcs.add_testcase(inputs, output)
    }
    tcs.generate();
    var ta_id = document.getElementById("ta-id-info").textContent;
    var txtarea = document.getElementById(ta_id);
    txtarea.value = tcs.content;
    close_modal("myModal")
    txtarea.focus();
}

function validate(element) {
    if (!element.checkValidity()) {
        element.reportValidity();
        return false;
    }
    return true
}

function create_div(id, class_name) {
    var div = document.createElement("div");
    div.className = class_name
    div.id = id;
    return div;
}

function create_label_input(div, id, lname, class_name) {
    var label = document.createElement("label");
    label.htmlFor = id;
    label.textContent = lname;
    var input = document.createElement("input");
    input.type = "text"
    input.required = true;
    input.id = id;
    input.name = id;
    input.className = class_name;
    div.append(label);
    div.append(input);
    return div;
}

function addtestcase() {
    var testcases = document.getElementById("testcases");
    var num_tcs = testcases.childElementCount;
    var n = document.getElementById("no_of_input").value;
    var div = create_div(num_tcs+1, "form-row");
    var col_div;
    for (var j = 0; j < n; j++) {
        var k = `in${num_tcs+1}${j+1}`
        col_div = create_div("","col")
        col_div = create_label_input(col_div, k, `Input ${j+1}`, `tc_in_${num_tcs+1} form-control`)
        div.append(col_div)
    }
    var o = `out${num_tcs+1}`
    col_div = create_div("","col")
    col_div = create_label_input(col_div, o, 'Output',`tc_out_${num_tcs+1} form-control`)
    div.append(col_div)
    testcases.append(div);
    document.getElementById("generate").hidden = false;
    document.getElementById("guide").hidden = false;
}

function create_options(arr) {
    var options = "";
    for (var value of arr) {
        options += `<option value=${value}>${value}</option>`;
    }
    return options
}

function addCon(n) {
    var in_on = document.getElementById("types");
    var testcases = document.getElementById("testcases");
    testcases.innerHTML = "";
    document.getElementById("generate").hidden = true;
    if (n > 0) {
        var language = document.getElementById("languages").value;
        if (language == 'Java') {
            var type_options = create_options(JAVA_TYPES);
        }
        else {
            var type_options = create_options(C_TYPES);
        }
        var html_content = "";
        for (var j = 0; j < n; j++) {
            html_content += `<div class="col">`
            html_content += `<label for="types${j+1}"> Input ${j+1} Type:</label>`
            html_content += `<select class="itypes form-control" id="types${j+1}" name="types${j+1}" required>`
            html_content += type_options
            html_content += "</select>"
            html_content += `</div>`
        }
        in_on.innerHTML = html_content;
        var out_content = `<div class="col">
            <label for="types_out"> Output Type:</label>
            <select id="types_out" class="form-control" name="types_out" required>
            </div>`;
        out_content += type_options;
        in_on.innerHTML += out_content;
        if (language == 'R' || language == 'Scilab' ) {
            in_on.style.display = "none";
        }
        document.getElementById("addtc").hidden = false;
        document.getElementById("reset").hidden = false;
    }
}

function show_modal(id, ta) {
  var modal = document.getElementById(id);
  modal.style.display = "block";
  document.getElementById("ta-id-info").textContent = ta;
}

function close_modal(id) {
  var modal = document.getElementById(id);
  modal.style.display = "none";
}
