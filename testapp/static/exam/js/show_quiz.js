    function my_confirm(frm)
      {
	   var r = confirm("Are you Sure ?");
	   if(r==false)
	   {  
		for(i=0;i<frm.quiz.length;i++)
		{
			frm.quiz[i].checked=false;
		}
		location.replace("{{URL_ROOT}}/exam/manage/showquiz");
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
			location.replace("{{URL_ROOT}}/exam/manage/showquiz");
      }
