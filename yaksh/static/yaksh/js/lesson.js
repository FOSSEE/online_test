$(document).ready(function() {
    var simplemde = new SimpleMDE({
        element: document.getElementById("id_description"),
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
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

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
        $("#loader").show();
        ajax_call($(this).attr("action"), 'POST', $(this).serializeArray());
    });

    function ajax_call(url, method, data) {
        $.ajax({
            url: url,
            timeout: 15000,
            type: method,
            data: JSON.stringify(data),
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            beforeSend: function(xhr, settings) {
              if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                var csrftoken = data[0].value
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
              }
            },
            success: function(msg) {
                $("#loader").hide();
                if (msg.success) {
                    if (msg.status) $("#lesson-content").html(msg.data);
                    if (msg.content_type === '1') {
                        add_topic();
                    }
                    else if(msg.content_type === '2') {
                        add_question();   
                    }
                }
                if (msg.message) alert(msg.message)
            },
            error: function(jqXHR, textStatus) {
                $("#loader").hide();
                alert("Cannot add the marker. Please try again");
            }
        });
    }

    function add_topic() {
        if (!$("#id_timer").val()) {
            $("#id_timer").val($("#vtimer").val());
        }
        $("#topic-form").submit(function(e) {
            e.preventDefault();
            $("#loader").show();
            ajax_call($(this).attr("action"), 'POST', $(this).serializeArray());
        });
    }

    function add_question() {
        if (!$("#id_timer").val()) {
            $("#id_timer").val($("#vtimer").val());
        }
        $("#question-form").submit(function(e) {
            e.preventDefault();
            $("#loader").show();
            ajax_call($(this).attr("action"), 'POST', $(this).serializeArray());
        });
    }

    $('#id_video_file').on('change',function(){
        //get the file name
        var files = [];
        for (var i = 0; i < $(this)[0].files.length; i++) {
            files.push($(this)[0].files[i].name);
        }
        $(this).next('.custom-file-label').html(files.join(', '));
    });

    $('#id_Lesson_files').on('change',function(){
        //get the file name
        var files = [];
        for (var i = 0; i < $(this)[0].files.length; i++) {
            files.push($(this)[0].files[i].name);
        }
        $(this).next('.custom-file-label').html(files.join(', '));
    });
});
