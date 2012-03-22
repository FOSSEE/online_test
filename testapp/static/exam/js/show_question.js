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
