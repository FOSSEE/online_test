$(document).ready(function(){
    $("#submit").click(function(){
        var selected_quiz = $("#id_quiz :selected").text();
        var video_session = $("#id_video_session").val();
        if(selected_quiz == "---------" && video_session.length == 0) {
            $("#alert").toggle();
            return false;
        }
        return true;
    });
});