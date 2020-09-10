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
            if(content.content != 1) {
                player.pause();
                url = $("#toc_"+content.id).val();
                ajax_call(url, "GET");
            }
        }
    });
});

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
    document.getElementById("ontop").style.display = "block";
}

function unlock_screen() {
    document.getElementById("ontop").style.display = "none";
}

function show_error(error) {
    var err_msg = "";
    Object.keys(err).forEach(function(key) {
        var value = err[key];
        err_msg = err_msg + key + " : " + value[0].message + "\n";
    });
    alert(err_msg);
}

function show_question(data) {
    $("#dialog").html(data);
    $("#dialog").dialog({
        width: 600,
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
    var toc_time = $("#toc_time_"+toc_id).val();
    player.currentTime = get_time_in_seconds(toc_time);
    url = $("#toc_"+toc_id).val();
    ajax_call(url, "GET");
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
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
            if(msg.message) alert(msg.message);
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