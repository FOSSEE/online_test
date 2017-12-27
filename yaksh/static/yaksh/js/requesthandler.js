request_status = "initial";
count = 0;
MAX_COUNT = 14

function reset_values() {
    request_status = "initial";
    count = 0;
}
function check_state(state, uid) {
    if ((state == "running" || state == "not started") && count < MAX_COUNT) {
        count++;
        setTimeout(function() {get_result(uid);}, 2000);
    } else if (state == "unknown") {
        reset_values();
        notify("Request timeout. Try again later.");
        unlock_screen();
    } else {
        reset_values()
        notify("Please try again.");
        unlock_screen();
    }
}

function notify(text) {
    var notice = document.getElementById("notification");
    notice.classList.add("alert");
    notice.classList.add("alert-success");
    notice.innerHTML = text;
}

function lock_screen() {
    document.getElementById("ontop").style.display = "block";
}

function unlock_screen() {
    document.getElementById("ontop").style.display = "none";
}

function show_skip() {
    document.getElementById("skip_ex").style.visibility = "visible";
}

function get_result(uid){
    var url = "/exam/get_result/" + uid + "/" + course_id + "/" + module_id + "/";
    ajax_check_code(url, "GET", "html", null, uid)
}

function response_handler(method_type, content_type, data, uid){
    if(content_type.indexOf("text/html") !== -1) {
        if( method_type === "POST") {
            reset_values();
        }
        unlock_screen();
        document.open();
        document.write(data);
        document.close();
    } else if(content_type.indexOf("application/json") !== -1) {
        res = JSON.parse(data);
        request_status = res.status;
        if (request_status){
          if(method_type === "POST") {
              uid = res.uid;
          }
          check_state(request_status, uid);
        }
        else{
          unlock_screen();
          if ($("#notification")){
            $("#notification").toggle();
          }

          var error_output = document.getElementById("error_panel");
          error_output.innerHTML = res.error;
          focus_on_error(error_output);
        }
    } else {
        reset_values();
        unlock_screen();
    }
}

function focus_on_error(ele){
    if (ele) {
      ele.scrollIntoView(true);
      window.scrollBy(0, -15);
        }
    }

function ajax_check_code(url, method_type, data_type, data, uid) {
    $.ajax({
        method: method_type,
        url: url,
        data: data,
        dataType: data_type,
        success: function(data, status, xhr) {
            content_type = xhr.getResponseHeader("content-type");
            response_handler(method_type, content_type, data, uid)
        },
        error: function(xhr, text_status, error_thrown ) {
            reset_values();
            unlock_screen();
            notify("There is some problem. Try later.")
        }
    });

}

var global_editor = {};

$(document).ready(function(){
  if(is_exercise == "True" && can_skip == "False"){
      setTimeout(function() {show_skip();}, delay_time*1000);
  }
  // Codemirror object, language modes and initial content
  // Get the textarea node
  var textarea_node = document.querySelector('#answer');

  var mode_dict = {
    'python': 'python',
    'c': 'text/x-csrc',
    'cpp': 'text/x-c++src',
    'java': 'text/x-java',
    'bash': 'text/x-sh',
    'scilab': 'text/x-csrc'
  }

  // Code mirror Options
  var options = {
      mode: mode_dict[lang],
      gutter: true,
      lineNumbers: true,
      onChange: function (instance, changes) {
          render();
      }
  };

  // Initialize the codemirror editor
  global_editor.editor = CodeMirror.fromTextArea(textarea_node, options);

  // Setting code editors initial content
  global_editor.editor.setValue(init_val);

  $('#code').submit(function(e) {
    lock_screen();
    var data = $(this).serializeArray();
    ajax_check_code($(this).attr("action"), "POST", "html", data, null)
        e.preventDefault(); // To stop the default form submission.
  });

  reset_editor = function() {
      global_editor.editor.setValue(init_val);
      global_editor.editor.clearHistory();
  }


});
