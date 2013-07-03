function confirm_delete(frm)
{
    var n=0;
    quiz = document.getElementsByName('quiz');
    for (var i =0;i<quiz.length;i++)
    {   
		if (quiz[i].checked == false)
			n = n + 1 ;
	}
    if(n==quiz.length)
    {
        alert("Please Select at least one Quiz");
        return false;
    }
    var r = confirm("Are you Sure ?");
	if(r==false)
	{  
		for(i=0;i<quiz.length;i++)
		{
			quiz[i].checked=false;
		}
        return false;
	}
}
function confirm_edit(frm)
{
    var n = 0;
    quiz = document.getElementsByName('quiz');
    for (var i =0;i<quiz.length;i++)
	{
		if (quiz[i].checked == false)
			n = n + 1 ;
	}
	if(n == quiz.length)
    {
        alert("Please Select at least one Question");
	    return false;
    }
    else
        return true;
}
