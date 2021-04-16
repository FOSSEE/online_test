$(document).ready(function() {
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('active');
    });

    $(document).ready(() => {
         $(function() {
            tinymce.init({
                selector: 'textarea#id_description',
                setup : function(ed) {
                      ed.on('change', function(e) {
                         tinymce.triggerSave();
                      });
                },
                max_height: 400,
                height: 200,
                plugins: "image code link",
                convert_urls: false
            });
        });
    });

    player = new Plyr('#player');
    var totalSeconds;
    store_video_time(contents_by_time);
    var time_arr_length = video_time.length;
    var total_duration;
    player.on('ready loadedmetadata', event => {
        total_duration = parseInt(player.duration);
        store_tracker_time(total_duration);
        $("#video_duration").val(get_time_in_hrs(total_duration));
    });

    player.on('timeupdate', event => {
        var current_time = player.currentTime;
        $("#current_video_time").val(get_time_in_hrs(current_time));
        if (time_arr_length > 0 && current_time >= video_time[loc]) {
            var content = contents_by_time[loc]; 
            loc += 1;
            if(content.content == 1) {
                show_topic($("#toc_desc_"+content.id).val(), false);
            }
            else {
                if(player.fullscreen.active) player.fullscreen.exit();
                player.pause()
                url = $("#toc_"+content.id).val();
                ajax_call(url, "GET", screen_lock=true);
            }
        }
        if(markers.length > 0 && current_time >= markers[track_count]) {
            track_count++;
            var csrf = document.getElementById("track-form").elements[0].value;
            ajax_call($("#track-form").attr("action"), $("#track-form").attr("method"),
                      $("#track-form").serialize(), csrf, screen_lock=false);
        }
    });
    player.on('ended', event => {
        var csrf = document.getElementById("track-form").elements[0].value;
        ajax_call($("#track-form").attr("action"), $("#track-form").attr("method"),
                  $("#track-form").serialize(), csrf, screen_lock=false);
        window.location.href = $("#next_unit").attr("href");
    });
});

function store_tracker_time(duration) {
    marker = duration / 4;
    for(var i = marker; i <= duration - marker; i = i + marker) {
        markers.push(i);
    }
}

function show_topic(description, override) {
    var topic_div = $("#topic-description");
    if(override) {
        topic_div.html(description);
    } else {
        topic_div.append("<br>" + description);
    }
}

function store_video_time(contents) {
    if(contents) {
        for (var j = 0; j < contents.length; j++)
        video_time.push(get_time_in_seconds(contents[j].time));
    }
}

function get_time_in_seconds(time) {
    var time = time.split(":");
    var hh = parseInt(time[0]);
    var mm = parseInt(time[1]);
    var ss = parseInt(time[2]);
    return hh * 3600 + mm * 60 + ss;
}

function get_time_in_hrs(time) {
    totalSeconds = parseInt(time)
    hours = Math.floor(totalSeconds / 3600);
    totalSeconds %= 3600;
    minutes = Math.floor(totalSeconds / 60);
    seconds = totalSeconds % 60;
    hours = hours < 10 ? "0" + hours : hours;
    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;
    return hours + ":" + minutes + ":" + seconds;
}

function lock_screen() {
    document.getElementById("loader").style.display = "block";
    if ($("#check").is(":visible")) {
        $("#check").attr("disabled", true);
    }
}

function unlock_screen() {
    document.getElementById("loader").style.display = "none";
    if ($("#check").is(":visible")) {
        $("#check").attr("disabled", false);
    }
}

function show_question(data) {
    $("#myModal").modal({backdrop: 'static', keyboard: false});
    $("#lesson_quiz_question").html(data)
    $("#submit-quiz-form").submit(function(e) {
        e.preventDefault();
        lock_screen();
        var csrf = document.getElementById("submit-quiz-form").elements[0].value;
        ajax_call($(this).attr("action"), $(this).attr("method"),
                  $(this).serialize(), csrf, screen_lock=true);
    });
}

function select_toc(element) {
    var toc_id = element.getAttribute("data-toc"); 
    var content_type = element.getAttribute("data-toc-type");
    var toc_time = $("#toc_time_"+toc_id).html().trim();
    player.currentTime = get_time_in_seconds(toc_time);
    if (content_type == 1) {
        show_topic($("#toc_desc_"+toc_id).val(), true);
    }
    else {
        url = $("#toc_"+toc_id).val();
        ajax_call(url, "GET");
    }
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function show_message(message, msg_type) {
    toastr.options = {
      "positionClass": "toast-top-center",
      "timeOut": "1500",
      "showDuration": "300",
    }
    switch(msg_type) {
        case "info": {
            toastr.info(message);
            break;
        }
        case "error": {
            toastr.error(message);
            break;
        }
        case "warning": {
            toastr.warning(message);
            break;
        }
        case "success": {
            toastr.success(message);
            break;
        }
        default: {
            toastr.info(message);
            break;
        }
    }
}

function ajax_call(url, method, data, csrf, screen_lock=true) {
    if(screen_lock) {lock_screen();}
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
            if (msg.data) {
                show_question(msg.data);
            }
            if (msg.message) {
                $("#myModal").modal('hide');
                if (msg.success) {
                    show_message(msg.message, "success");
                }
                else {
                    show_message(msg.message, "warning");
                }
            }
        },
        error: function(xhr, data) {
            unlock_screen();
            switch(xhr.status) {
                case 400: {
                    show_message("400 status code! server error", "error");
                    break;
                }
                case 500: {
                    show_message("500 status code! server error", "error");
                    break;
                }
                case 404: {
                    show_message("404 status code! server error", "error");
                    break;
                }
                default: {
                    show_message('Unable to perform action. Please try again', "error");
                    break;
                }
            }
        }
    });
}