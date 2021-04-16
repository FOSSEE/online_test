function confirm_delete(frm)
{
    var n=0;
    for (var i =0;i<frm.question.length;i++)
    {   
		if (frm.question[i].checked == false)
			n = n + 1 ;
	}
    if(n==frm.question.length)
    {
        alert("Please Select at least one Question");
        return false;
    }
    var r = confirm("Are you Sure ?");
	if(r==false)
	{  
		for(i=0;i<frm.question.length;i++)
		{
			frm.question[i].checked=false;
		}
        return false;
	}
}
function confirm_edit(frm)
{
    var n = 0;
    for (var i =0;i<frm.question.length;i++)
	{
		if (frm.question[i].checked == false)
			n = n + 1 ;
	}
	if(n == frm.question.length)
    {
        alert("Please Select at least one Question");
	    return false;
    }
    else
        return true;
}

function append_tag(tag){
    var tag_name = document.getElementById("question_tags");
    if (tag_name.value != null){
        tag_name.value = tag.value+", "+tag_name.value;
    }
    else{
        tag_name.value = tag.value;
    }
}
$(document).ready(function() {
    $("#questions-table").tablesorter({});
    $("#checkall").change(function(){
        if($(this).prop("checked")) {
                $("#filtered-questions input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#filtered-questions input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });
    if(/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
      $("#question-list").removeClass("col-9");
      $("#question-list").addClass("col");
    } else{
      $("#question-list").addClass("col-9");
      $("#question-list").removeClass("col");
    }
});
