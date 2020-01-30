$(document).ready(function(){
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();

    function csrfSafeMethod(method) {
        // These HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    $("#preview").click(function(){
        var description = $("#id_description").val();
        var preview_url = window.location.protocol + "//" +
                window.location.host + "/exam/manage/courses/lesson/preview/";
        $.ajax({
            url: preview_url,
            timeout: 15000,
            type: 'POST',
            data: JSON.stringify({'description': description}),
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            success: function(msg) {
                preview_text(msg['data']);
            },
            error: function(jqXHR, textStatus) {

            }
        });
    });

    function preview_text(data){
        var preview_div = $("#preview_text_div");
        if (!preview_div.is(":visible")){
            $("#preview_text_div").toggle();
        }
        $("#description_body").empty();
        $("#description_body").append(data);
    }

    $("#embed").click(function() {
        $("#dialog_iframe").toggle();
        $("#dialog_iframe").dialog({
            resizable: true,
            height: '450',
            width: '640'
        });
    });

    $("#submit_info").click(function(){
        var url = $("#url").val();
        if (url == "") {
            if (!$("#error_div").is(":visible")){
                $("#error_div").toggle();
            }
        }
        else{
            if ($("#error_div").is(":visible")){
                $("#error_div").toggle();
            }
            $("#video_frame").attr("src", url);
            $("#html_text").text($("#iframe_div").html().trim());
        }
    });

    $("#copy").click(function(){
        try{
            var text = $("#html_text");
            text.select();
            document.execCommand("Copy");
        } catch (err) {
            alert("Unable to copy. Press Ctrl+C or Cmd+C to copy")    
        }
    });

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
