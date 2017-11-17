$(document).ready(function(){
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie("csrftoken");
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
});