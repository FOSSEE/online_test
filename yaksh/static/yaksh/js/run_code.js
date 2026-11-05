(function(){
    var POLL_INTERVAL_MS = 1000;
    var MAX_POLLS = 20;
    var running = false;
    var run_marker = null;
    var msg = null;

    function el(id){
        return document.getElementById(id);
    }

    function set_status(text, css_class){
        var status = el("run_status")
        status.textContent = text;
        status.className = "small ml-3 " + (css_class || "text-muted");
    }

    function finish(){
        running = false;
        var button = el("run_code")
        button.disabled = false;
        button.innerHTML = '<i class="fa fa-play"></i>&nbsp;Run';
        button.blur();
    }

    function clear_marker(){
        if(run_marker){
            run_marker.clear();
            run_marker = null;
        }
    }

    function mark_error_line(line_no){
        var editor = global_editor.editor;
        clear_marker();
        if(!editor || !line_no ||line_no > editor.lineCount()){
            return;
        }
        var line = line_no - 1;
        var start_point = {line: line, ch: 0}
        var end_point = {line: line, ch: editor.getLine(line).length}
        run_marker = editor.markText(start_point, end_point,
            {className: "activeline", clearOnEnter: true});
    }

    function error_start(output){
        var markers = ["Traceback (most recent call last):", '  File "main.py"'];
        for(var i = 0; i < markers.length; i++){
            var index = output.indexOf(markers[i])
            if(index != -1){
                return index;
            }
        }
        return -1
    }

    function show_output(result){
        var pre = el("run_output");
        var output = result.output || "";
        pre.textContent = "";

        var split = result.exit_code ? error_start(output) : -1
        var normal = split === -1 ? output : output.slice(0, split);
        var error = split === -1? "" : output.slice(split);
        if(normal){
            pre.appendChild(document.createTextNode(normal));
        }
        if(error){
            var span = document.createElement("span");
            span.className = "run-error";
            span.textContent = error;
            pre.appendChild(span);
        }
        if(!output){
            var empty = document.createElement("span");
            empty.className = "text-muted";
            empty.textContent = "(no output)";
            pre.appendChild(empty);
        }

        var hint = el("run_hint")
        hint.textContent = result.hint || "";
        hint.style.display = result.hint ? "block": "none";

        if(result.timed_out){
            msg = "Stopped: code took too long to run. Check for an infinte loop.";
            set_status(msg, "text-danger");
        } else if(result.truncated){
            msg = "Output cut at 10,000 characters."
            set_status(msg, "text-warning");
        } else if(result.exit_code){
            msg = "Stopped with an error."
            set_status(msg, "text-danger");
        } else {
            msg = "Ran successfully."
            set_status(msg, "text-success");
        }
        mark_error_line(result.error_line);
    }

    function show_problem(message){
        el("run_output").textContent = "";
        el("run_hint").style.display = "none";
        set_status(message, "text-danger");
    }

    function poll(url, count){
        $.ajax({
            method: "GET",
            url: url,
            dataType: "json",
            success: function(result){
                if(result.status === "done"){
                    show_output(result);
                    finish();
                } else if((result.status ==="running" ||
                          result.status === "not started") && count < MAX_POLLS) {
                    setTimeout(function(){poll(url, count+1);}, POLL_INTERVAL_MS);
                } else {
                    show_problem("No result from the code server. Please try again");
                    finish();
                }
            },
            error: function(xhr){
                var message = (xhr.responseJSON && xhr.responseJSON.message) ||
                    "Could not get the result. Please try again."
                show_problem(message);
                finish();
            }
        });
    }

    function run(){
        var button = el("run_code");
        if(running || !button || !global_editor.editor){
            return;
        }
        running = true;
        button.disabled = true;
        button.innerHTML = '<i class="fa fa-spinner fa-spin"></i>&nbsp;Running';
        el("run_panel").style.display = "block";
        el("run_output").textContent = "";
        el("run_hint").style.display = "none";
        set_status("Running...");
        clear_marker();

        $.ajax({
            method: "POST",
            url: button.dataset.runUrl,
            dataType: "json",
            data: {
                answer: global_editor.editor.getValue(),
                stdin: el("run_stdin").value,
                csrfmiddlewaretoken: document.querySelector(
                    "#code [name=csrfmiddlewaretoken]"
                ).value,
            },
            success: function(response){
                if(response.status == "running"){
                    var url = button.dataset.resultUrl.replace("RUN_UID", response.uid);
                    setTimeout(function(){poll(url, 1);}, POLL_INTERVAL_MS / 2);
                } else {
                    show_problem(response.message || "Could not run the code");
                    finish();
                }
            },
            error: function(xhr){
                var message = (xhr.responseJSON && xhr.responseJSON.message) ||
                  "Could not run the code. Please try again.";
                show_problem(message);
                finish();
            }
        });
    }

    $(document).ready(function(){
        var button = el("run_code");
        if(!button){
            return;
        }
        button.addEventListener("click", run);
        el("run_close").addEventListener("click", function(){
            el("run_panel").style.display = "none";
            clear_marker();
        });
        el("toggle_stdin").addEventListener("click", function(e){
            e.preventDefault();
            var box = el("stdin_box");
            var open = box.style.display !== "none";
            box.style.display = open ? "none" : "block";
            this.setAttribute("aria-expanded", String(!open));
            if(!open){
                el("run_stdin").focus();
            }
        });
        if(global_editor.editor){
            global_editor.editor.addKeyMap({
                "Ctrl-Enter": run,
                "Cmd-Enter": run
            });
        }
    });

})();
