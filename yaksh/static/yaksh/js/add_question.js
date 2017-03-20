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
    $("[id*="+'test_case_args'+"]").attr('placeholder',
                                         'Command Line arguments for bash only');

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


    $('#id_type').bind('focus', function(event){
        var type = document.getElementById('id_type');
        type.style.border = '1px solid #ccc';
    });

    $('#id_language').bind('focus', function(event){
        var language = document.getElementById('id_language');
        language.style.border = '1px solid #ccc';
    });
	document.getElementById('my').innerHTML = document.getElementById('id_description').value ;


    if (document.getElementById('id_grade_assignment_upload').checked ||
        document.getElementById('id_type').val() == 'upload'){
        $("#id_grade_assignment_upload").prop("disabled", false);
    }
    else{
        $("#id_grade_assignment_upload").prop("disabled", true);
    }

    $('#id_type').change(function() {
        if ($(this).val() == "upload"){
            $("#id_grade_assignment_upload").prop("disabled", false);
        }
        else{
            $("#id_grade_assignment_upload").prop("disabled", true);
        }
   });
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

}
