$(document).ready(function() {
    var simplemde = new SimpleMDE({
        element: document.getElementById("id_description"),
        forceSync: true,
    });
    const player = new Plyr('#player');
    var timer = $("#vtimer");
    var totalSeconds;
    player.on('timeupdate', event => {
      totalSeconds = parseInt(player.currentTime)
      hours = Math.floor(totalSeconds / 3600);
      totalSeconds %= 3600;
      minutes = Math.floor(totalSeconds / 60);
      seconds = totalSeconds % 60;
      hours = hours < 10 ? "0" + hours : hours;
      minutes = minutes < 10 ? "0" + minutes : minutes;
      seconds = seconds < 10 ? "0" + seconds : seconds;
      timer.val(hours + ":" + minutes + ":" + seconds);
    });

    $("#vtimer").on("change keyup paste", function() {
        player.pause();
        var time = $(this).val().split(":");
        var hh = parseInt(time[0]);
        var mm = parseInt(time[1]);
        var ss = parseInt(time[2]);
        player.currentTime = hh * 3600 + mm * 60 + ss;
    });

    $('#content-type').on('change', function (e) {
        var optionSelected = $("option:selected", this);
        var valueSelected = this.value;
        if (valueSelected == "" || valueSelected == "1") {
            $("#id_type").hide();
            $("#id_type").attr("required", false);
        } else {
            $("#id_type").show();
            $("#id_type").attr("required", true);
        }
    });
    
    // Marker Form
    $("#marker-form").submit(function(e) {
        e.preventDefault();
        lock_screen();
        var csrf = document.getElementById("marker-form").elements[0].value;
        ajax_call($(this).attr("action"), $(this).attr("method"), $(this).serialize(), csrf);
    });

    $('#id_video_file').on('change',function() {
        //get the file name
        var files = [];
        for (var i = 0; i < $(this)[0].files.length; i++) {
            files.push($(this)[0].files[i].name);
        }
        $(this).next('.custom-file-label').html(files.join(', '));
    });

    $('#id_Lesson_files').on('change',function() {
        //get the file name
        var files = [];
        for (var i = 0; i < $(this)[0].files.length; i++) {
            files.push($(this)[0].files[i].name);
        }
        $(this).next('.custom-file-label').html(files.join(', '));
    });
});


function add_topic() {
    if (!$("#id_timer").val()) {
        $("#id_timer").val($("#vtimer").val());
    }
    $("#topic-form").submit(function(e) {
        e.preventDefault();
        lock_screen();
        var csrf = document.getElementById("topic-form").elements[0].value;
        ajax_call($(this).attr("action"), $(this).attr("method"), $(this).serialize(), csrf);
    });
}

function add_question() {
    if (!$("#id_timer").val()) {
        $("#id_timer").val($("#vtimer").val());
    }
    $("#question-form").submit(function(e) {
        e.preventDefault();
        lock_screen();
        var csrf = document.getElementById("question-form").elements[0].value;
        ajax_call($(this).attr("action"), $(this).attr("method"), $(this).serialize(), csrf);
    });
}

function lock_screen() {
    document.getElementById("ontop").style.display = "block";
}

function unlock_screen() {
    document.getElementById("ontop").style.display = "none";
}

function show_error(error) {
    var err_msg = "\n";
    Object.keys(err).forEach(function(key) {
        var value = err[key];
        err_msg = err_msg + key + " : " + value[0].message + "\n";
    });
    alert(err_msg);
}

function show_toc(toc) {
    $("#lesson-content").empty();
    $("#toc").html(toc);
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function ajax_call(url, method, data, csrf) {
    $.ajax({
        url: url,
        timeout: 15000,
        method: method,
        data: data,
        beforeSend: function(xhr, settings) {
          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrf);
          }
        },
        success: function(msg) {
            unlock_screen();
            if (msg.success) {
                if (msg.status) $("#lesson-content").html(msg.data);
                if (parseInt(msg.content_type) === 1) {
                    add_topic();
                }
                else {
                    add_question();
                }
            }
            if (msg.toc) show_toc(msg.toc);
            if (msg.message) alert(msg.message)
        },
        error: function(xhr, data) {
            unlock_screen();
            switch(xhr.status) {
                case 400: {
                    err = JSON.parse(xhr.responseJSON.message);
                    show_error(err);
                    break;
                }
                case 500: {
                    alert('500 status code! server error');
                    break;
                }
                case 404: {
                    alert('404 status code! server error');
                    break;
                }
                default: {
                    alert('Unable to perform action. Please try again');
                    break;
                }
            }
        }
    });
}
