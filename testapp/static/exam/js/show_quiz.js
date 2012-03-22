function confirm_delete(frm)
{
    var n=0;
    for (var i =0;i<frm.quiz.length;i++)
    {   
		if (frm.quiz[i].checked == false)
			n = n + 1 ;
	}
    if(n==frm.quiz.length)
    {
        alert("Please Select at least one Quiz");
        return false;
    }
    var r = confirm("Are you Sure ?");
	if(r==false)
	{  
		for(i=0;i<frm.quiz.length;i++)
		{
			frm.quiz[i].checked=false;
		}
        return false;
	}
}
function confirm_edit(frm)
{
    var n = 0;
    for (var i =0;i<frm.quiz.length;i++)
	{
		if (frm.quiz[i].checked == false)
			n = n + 1 ;
	}
	if(n == frm.quiz.length)
    {
        alert("Please Select at least one Quiz");
	    return false;
    }
    else
        return true;
}
