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
});