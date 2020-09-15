$(document).ready(function() {
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('active');
    });

    $(function() {
        tinymce.init({
            selector: 'textarea#id_description',
            setup : function(ed) {
                  ed.on('change', function(e) {
                     tinymce.triggerSave();
                  });
            },
            max_height: 400,
            height: 400,
            plugins: "image code link",
            convert_urls: false
        });
    });
    
    player = new Plyr('#player');
    var totalSeconds;
    store_video_time(contents_by_time);
    var time_arr_length = video_time.length;
    player.on('timeupdate', event => {
        if (time_arr_length > 0 && player.currentTime >= video_time[loc]) {
            var content = contents_by_time[loc]; 
            loc += 1;
            if(content.content == 1) {
                show_topic($("#toc_desc_"+content.id).val(), false);
            }
            else {
                player.pause();
                if(player.fullscreen.active) player.fullscreen.exit();
                url = $("#toc_"+content.id).val();
                ajax_call(url, "GET");
            }
        }
    });
});

function show_topic(description, override) {
    var topic_div = $("#topic-description");
    if(override) {
        topic_div.html(description);
    } else {
        topic_div.append("<br>" + description);
    }
}

function store_video_time(contents) {
    for (var j = 0; j < contents.length; j++)
    video_time.push(get_time_in_seconds(contents[j].time));
}

function get_time_in_seconds(time) {
    var time = time.split(":");
    var hh = parseInt(time[0]);
    var mm = parseInt(time[1]);
    var ss = parseInt(time[2]);
    return hh * 3600 + mm * 60 + ss;
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
    $("#dialog").html(data);
    $("#dialog").dialog({
        width: 800,
        height: 500,
    });
    $("#submit-quiz-form").submit(function(e) {
        e.preventDefault();
        lock_screen();
        var csrf = document.getElementById("submit-quiz-form").elements[0].value;
        ajax_call($(this).attr("action"), $(this).attr("method"), $(this).serialize(), csrf);
    });
}

function select_toc(element) {
    var toc_id = element.getAttribute("data-toc"); 
    var content_type = element.getAttribute("data-toc-type");
    var toc_time = $("#toc_time_"+toc_id).val();
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

function ajax_call(url, method, data, csrf) {
    lock_screen();
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
                if (msg.success) {
                    $("#dialog").dialog("close");
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