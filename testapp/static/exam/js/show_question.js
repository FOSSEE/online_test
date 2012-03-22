function confirm_delete(frm)
      {
      	 var r = confirm("Are you Sure ?");
	 if(r==false)
         {
               for(i=0;i<frm.question.length;i++)
               {
                       frm.question[i].checked=false;
               }
               location.replace("{{URL_ROOT}}/exam/manage/showquestion");
         }
      }
      function confirm_edit(frm)
      {
	 var n = 0;
	 for(i=0;i<frm.question.length;i++)
	 {
		if(frm.question[i].checked==true)
			n = n+1;
	 }
   	 if(n==0)
		location.replace("{{URL_ROOT}}/exam/manage/showquestion");
      }
