function confirm_delete(frm)
{
    var n=0;
    test_case = document.getElementsByName('test_case');
    for (var i =0;i<test_case.length;i++)
    {   
		if (test_case[i].checked == false)
			n = n + 1 ;
	}
    if(n==test_case.length)
    {
        alert("Please Select at least one test case");
        return false;
    }
    var r = confirm("Are you Sure ?");
	if(r==false)
	{  
		for(i=0;i<test_case.length;i++)
		{
			test_case[i].checked=false;
		}
        return false;
	}
}