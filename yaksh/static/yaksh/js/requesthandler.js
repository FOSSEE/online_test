request_status = "initial"
count = 0;
checker = null
function submitRequest(){
    document.forms["code"].submit();
}

function check_state(state, uid) {
    if ((state == "running" || state == "not started") && count < 7) {
        count++;
        setTimeout(function() {get_result(uid);}, 2000);
    } else if (state == "unknown") {
        request_status = "initial";
        count = 0;
        notify("You are requesting for a wrong data");
        clearInterval(checker);
        unlock_screen();
    } else {
        request_status = "initial";
        count = 0;
        notify("Please try after few minutes");
        clearInterval(checker);
        unlock_screen();
    }
}

function notify(text) {
    var $notice = document.getElementById("notification");
    $notice.classList.add("alert");
    $notice.classList.add("alert-success");
    $notice.innerHTML = text;
}

function lock_screen() {
    document.getElementById("ontop").style.display = "block";
}

function unlock_screen() {
    document.getElementById("ontop").style.display = "none";
}

function check_lock_screen() {
    var $ontop_div = document.getElementById("ontop");
    if ($ontop_div.style.display == "block") {
        $ontop_div.style.display = "none";
    }
}

function get_result(uid){
    $.ajax({
        method: "GET",
        url: "/exam/get_results/"+uid+"/",
        dataType: "html", // Your server can response html, json, xml format.
        success: function(data, status, xhr) {
            content_type = xhr.getResponseHeader("content-type");
            if(content_type.includes("text/html")) {
                clearInterval(checker);
                unlock_screen();
                document.open();
                document.write(data);
                document.close();
            } else if(content_type.includes("application/json")) {
                res = JSON.parse(data);
                request_status = res.status;
                check_state(request_status, uid);
            } else {
                request_status = "initial";
                count = 0;
                clearInterval(checker);
                unlock_screen();
            }
        },
        error: function(xhr, text_status, error_thrown ) {
            request_status = "initial";
            count = 0;
            clearInterval(checker);
            unlock_screen();
            notify("There is some problem. Try later.")
        }
    });
}

var global_editor = {};
$(document).ready(function(){
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

  function reset_editor() {
      global_editor.editor.setValue(init_val);
      global_editor.editor.clearHistory();
  }
    $('#code').submit(function(e) {
      checker = setInterval(check_lock_screen, 30000);
      lock_screen();
      $.ajax({
            type: 'POST',
            url: $(this).attr("action"),
            data: $(this).serializeArray(),
            dataType: "html", // Your server can response html, json, xml format.
            success: function(data, status, xhr) {
                content_type = xhr.getResponseHeader("content-type");
                if(content_type.includes("text/html")) {
                    request_status = "initial"
                    count = 0;
                    clearInterval(checker);
                    unlock_screen();
                    document.open();
                    document.write(data);
                    document.close();
                } else if(content_type.includes("application/json")) {
                    res = JSON.parse(data);
                    var uid = res.uid;
                    request_status = res.state;
                    check_state(request_status, uid);
                } else {
                    request_status = "initial";
                    count = 0;
                    clearInterval(checker);
                    unlock_screen();
                }
            },
            error: function(xhr, text_status, error_thrown ) {
                request_status = "initial";
                count = 0;
                clearInterval(checker);
                unlock_screen();
                notify("There is some problem. Try later.")
            }
          });
          e.preventDefault(); // To stop the default form submission.
    });
});
