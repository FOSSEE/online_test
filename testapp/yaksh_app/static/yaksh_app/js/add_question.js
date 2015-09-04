function increase(frm)
{
	if(frm.points.value == "")
	{
		frm.points.value = "0.5";
		return;
	}
	frm.points.value = parseFloat(frm.points.value) + 0.5;
}

function decrease(frm)
{
	if(frm.points.value > 0)
	{
		frm.points.value = parseFloat(frm.points.value) - 0.5;
	}
	else
	{
		frm.points.value=0;
	}

	
}

function setSelectionRange(input, selectionStart, selectionEnd) 
{
    if (input.setSelectionRange) 
    {
		input.focus();
		input.setSelectionRange(selectionStart, selectionEnd);
    }
    else if (input.createTextRange) 
    {
		var range = input.createTextRange();
		range.collapse(true);
		range.moveEnd('character', selectionEnd);
		range.moveStart('character', selectionStart);
		range.select();
    }
}

function replaceSelection (input, replaceString) 
{
    if (input.setSelectionRange) 
    {
		var selectionStart = input.selectionStart;
		var selectionEnd = input.selectionEnd;
		input.value = input.value.substring(0, selectionStart)+ replaceString + input.value.substring(selectionEnd);
		if (selectionStart != selectionEnd)
		{ 
			setSelectionRange(input, selectionStart, selectionStart + 	replaceString.length);
		}
		else
		{
			setSelectionRange(input, selectionStart + replaceString.length, selectionStart + replaceString.length);
		}
    }
    else if (document.selection) 
    {
		var range = document.selection.createRange();
		if (range.parentElement() == input) 
		{
			var isCollapsed = range.text == '';
			range.text = replaceString;
			if (!isCollapsed)  
			{
				range.moveStart('character', -replaceString.length);
				range.select();
			}
		}
    }
}

function textareaformat()
{
	document.getElementById('id_type').setAttribute('class','select-type');
	document.getElementById('id_points').setAttribute('class','mini-text');
    document.getElementById('id_tags').setAttribute('class','tag-text');
    
	
	$('#id_snippet').bind('keydown', function( event ){
         if(navigator.userAgent.match("Gecko"))
		{
			c=event.which;
		}
		else
		{
			c=event.keyCode;
		}
		if(c==9)
		{
			replaceSelection(document.getElementById('id_snippet'),String.fromCharCode(9));
			setTimeout(document.getElementById('id_snippet'),0);	
			return false;
		}
      });
      	
	$('#id_description').bind('focus', function( event ){
         document.getElementById("id_description").rows=5;
         document.getElementById("id_description").cols=40;
      });

	$('#id_description').bind('blur', function( event ){
         document.getElementById("id_description").rows=1;
         document.getElementById("id_description").cols=40;
      });
	
	$('#id_description').bind('keypress', function (event){
		document.getElementById('my').innerHTML = document.getElementById('id_description').value ;
	});

	$('#id_test').bind('focus', function( event ){
         document.getElementById("id_test").rows=5;
         document.getElementById("id_test").cols=40;
      });

	$('#id_test').bind('blur', function( event ){
         document.getElementById("id_test").rows=1;
         document.getElementById("id_test").cols=40;
      });
      
	$('#id_options').bind('focus', function( event ){
         document.getElementById("id_options").rows=5;
         document.getElementById("id_options").cols=40;
      });
	$('#id_options').bind('blur', function( event ){
         document.getElementById("id_options").rows=1;
         document.getElementById("id_options").cols=40;
      });
      
      $('#id_snippet').bind('focus', function( event ){
         document.getElementById("id_snippet").rows=5;
         document.getElementById("id_snippet").cols=40;
      });
	$('#id_snippet').bind('blur', function( event ){
         document.getElementById("id_snippet").rows=1;
         document.getElementById("id_snippet").cols=40;
      });


        $('#id_type').bind('focus', function(event){
            var type = document.getElementById('id_type');
            type.style.border = '1px solid #ccc';
        });

        $('#id_language').bind('focus', function(event){
            var language = document.getElementById('id_language');
            language.style.border = '1px solid #ccc';
        });
	
	$('#id_type').bind('change',function(event){
		var value = document.getElementById('id_type').value;
		if(value == 'mcq' || value == 'mcc')
		{
			document.getElementById('id_options').style.visibility='visible';
			document.getElementById('label_option').innerHTML="Options :";
		}
		else
		{
			document.getElementById('id_options').style.visibility='hidden';
			document.getElementById('label_option').innerHTML = "";
		}
	});
		document.getElementById('my').innerHTML = document.getElementById('id_description').value ;
		var value = document.getElementById('id_type').value;
		if(value == 'mcq' || value == 'mcc')
		{
			document.getElementById('id_options').style.visibility='visible';
			document.getElementById('label_option').innerHTML="Options :"
		}
		else
		{
			document.getElementById('id_options').style.visibility='hidden';
			document.getElementById('label_option').innerHTML = "";
		}	
}

function autosubmit()
{
        var language = document.getElementById('id_language');
        if(language.value == 'select')
        {
            language.style.border="solid red";
            return false;
        }
        var type = document.getElementById('id_type');
        if(type.value == 'select')
        {
            type.style.border = 'solid red';
            return false;
		}


	if (type.value == 'mcq' || type.value == 'mcc')
	{
		var value = document.getElementById('id_options').value;
		if(value.split('\n').length < 4)
		{
			alert("Please Enter 4 options. One option per line.");
			return false;
		}
		return true;
	}

}
