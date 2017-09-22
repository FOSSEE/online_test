$(document).ready(function(){

    // Check if website is being in mobile browser or web
    var isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    if (isMobile) {
        $("#result-table").css("z-index", "1000").css("position", "relative");
    } else {
        $("#result-table").css("z-index", "2001").css("position", "relative");
    }

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
    var user_id, que_id, answer_paper_id, answers_list;

    $('.item').click(function() {
        var data = $(this).data('item-id');
        user_id = data.split("_")[0];
        que_id = data.split("_")[1];
        answer_paper_id = data.split("_")[2]
        var request_url = window.location.protocol + "//" +
                    window.location.host + "/exam/manage/get_question_answer/" +
                    answer_paper_id + "/" + user_id + "/" + que_id;
        get_answers(request_url);
    });

    $("#view_all_answers").click(function() {
        var answers = [];
        for (var i=0; i < answers_list.length; i++){
            answers.push("<pre>" + answers_list[i]+ "</pre>" + "<br>");
        }
        $("#latest_ans").html(answers)
    });

    function get_answers(get_url) {
        $.ajax({
            url: get_url,
            timeout:15000,
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
    }

    function show_dialog(data){
        answers_list = data.answer;
        $("#question").html(data.question);
        $("#latest_ans").html("<pre>" + answers_list[data.answer.length - 1] + "</pre>");
        $("#user").text(data.user);
        $("#dialog").dialog({
            height: $(window).height() * .5,
            maxHeight: $(window).height() * .5,
            width: $(window).width() * .5,
            maxwidth: $(window).height() * .5
        });
    }
});
