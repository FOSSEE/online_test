$(document).ready(function(){
    $("#result-table").tablesorter({sortList: [[5,1]]});
    var papers_length = $("#papers").val();
    for (var i=0; i < papers_length; i++) {
        var paper_status = $("#status"+[i]);
        var hh, mm, ss;
        var time_left = $("#time_left"+[i]);
        if (paper_status.text() == "completed"){
            hh = "-";
            mm = "-";
            ss = "-";
        }
        else{
            var time = time_left.text();
            hh   = Math.floor(time / 3600);
            mm = Math.floor((time - (hh * 3600)) / 60);
            ss = time - (hh * 3600) - (mm * 60);
        }
        time_left.text(hh + ":" + mm + ":" + ss);
    }

    $('.item').click(function() {
        var data = $(this).data('item-id');
        var user_id = data.split("_")[0];
        var que_id = data.split("_")[1];
        var answer_paper_id = data.split("_")[2]
        var request_url = window.location.protocol + "//" +
                    window.location.host + "/exam/manage/get_question_answer/" +
                    answer_paper_id + "/" + user_id + "/" + que_id;
        $.ajax({
            url: request_url,
            timeout:30000,
            type: "GET",
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            success: function(msg) {
                show_dialog(msg);
            },
            error: function(jqXHR, textStatus) {
                alert("Unable to get answers. Please Try again later.");
            }
        });
    });

    function show_dialog(data){
        $("#question").html(data.question);
        $("#latest_ans").html(data.answer);
        $("#user").text(data.user);
        $("#dialog").dialog({
            height: $(window).height() * .5,
            maxHeight: $(window).height() * .5,
            width: $(window).width() * .5,
            maxwidth: $(window).height() * .5
        });
    }
});
